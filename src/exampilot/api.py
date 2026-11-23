import hashlib
import hmac
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from . import agent, quiz, stats, storage
from .config import settings
from .db import open_pool, pool
from .jobqueue import connect

Course = Literal["daa", "swe", "ai"]
MAX_UPLOAD = 30 * 1024 * 1024  # Cloud Run caps request bodies at 32 MiB


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .ingest.embedder import Embedder
    from .retrieval import Retriever
    from .worker import load_classifier

    open_pool()
    app.state.embedder = Embedder(settings.embed_model)  # once, not per request
    app.state.retriever = Retriever(app.state.embedder, router=load_classifier())
    app.state.queue = connect(settings.redis_url)
    yield
    pool.close()


app = FastAPI(title="ExamPilot", lifespan=lifespan)


def auth(authorization: Annotated[str, Header()] = "") -> None:
    expected = f"Bearer {settings.api_token}"
    if not settings.api_token or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="unauthorized")


# Endpoints are plain `def` on purpose: Claude and psycopg calls block, and FastAPI
# runs sync endpoints in a thread pool. `async def` here would stall the whole server.

@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/readyz")
def readyz(request: Request):
    with pool.connection() as conn:
        conn.execute("SELECT 1")
    request.app.state.queue.r.ping()
    return {"ok": True}


@app.post("/documents", dependencies=[Depends(auth)])
def upload(request: Request, course: Annotated[Course, Form()], file: UploadFile):
    data = file.file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "file too large, split it or use the CLI")
    name = Path(file.filename or "upload").name
    if not (data.startswith(b"%PDF") or name.lower().endswith(".md")):
        raise HTTPException(400, "only PDF or Markdown files")

    doc_id = hashlib.sha256(data).hexdigest()
    path = storage.save(f"{doc_id}{Path(name).suffix.lower()}", data)
    with pool.connection() as conn:
        row = conn.execute(
            "INSERT INTO documents (id, course_id, filename, path) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO NOTHING RETURNING id",
            (doc_id, course, name, path),
        ).fetchone()
    if row is None:
        return {"document_id": doc_id, "status": "duplicate"}
    # if we die right here the doc stays 'queued'; `cli requeue-stuck` picks it up
    request.app.state.queue.enqueue({"document_id": doc_id})
    return {"document_id": doc_id, "status": "queued"}


@app.get("/documents", dependencies=[Depends(auth)])
def list_documents(request: Request):
    return {"documents": stats.documents(), "queue": request.app.state.queue.stats()}


@app.get("/files/{doc_id}", dependencies=[Depends(auth)])
def get_file(doc_id: str):
    with pool.connection() as conn:
        row = conn.execute("SELECT path, filename FROM documents WHERE id = %s",
                           (doc_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "no such document")
    path, filename = row
    media = "text/markdown" if filename.lower().endswith(".md") else "application/pdf"
    return Response(storage.load(path), media_type=media,
                    headers={"Content-Disposition": f'inline; filename="{filename}"'})


@app.get("/search", dependencies=[Depends(auth)])
def search(request: Request, q: str, course: Course | None = None, k: int = 6):
    hits = request.app.state.retriever.search(q, course=course, k=min(k, 20))
    return [h.to_dict() for h in hits]


class ChatIn(BaseModel):
    conversation_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=4000)


@app.post("/chat", dependencies=[Depends(auth)])
def chat(body: ChatIn, request: Request):
    conv = body.conversation_id or uuid.uuid4()
    with pool.connection() as conn:
        history = [{"role": r, "content": c} for r, c in conn.execute(
            "SELECT role, content FROM chat_messages WHERE conversation_id = %s ORDER BY seq",
            (conv,),
        )]

    result = agent.run(history, body.message, request.app.state.retriever)
    if result.refused:
        return {
            "conversation_id": conv,
            "refused": True,
            "parts": [{"text": "I can't help with that one. Try rephrasing.", "refs": []}],
            "sources": [],
        }

    with pool.connection() as conn, conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO chat_messages (conversation_id, seq, role, content) "
            "VALUES (%s, %s, %s, %s)",
            [(conv, len(history) + i, m["role"], Jsonb(agent.to_jsonable(m["content"])))
             for i, m in enumerate(result.new_messages)],
        )
    return {"conversation_id": conv, **agent.render(result.final)}


@app.post("/quiz/next", dependencies=[Depends(auth)])
def quiz_next(course: Course):
    q = quiz.next_question(course)
    hidden = {"answer", "explanation", "source_chunk_ids", "model"}
    return {k: v for k, v in q.items() if k not in hidden}


class AnswerIn(BaseModel):
    question_id: uuid.UUID
    answer: str = Field(min_length=1, max_length=4000)


@app.post("/quiz/answer", dependencies=[Depends(auth)])
def quiz_answer(body: AnswerIn):
    try:
        return quiz.submit_answer(str(body.question_id), body.answer)
    except KeyError as e:
        raise HTTPException(404, str(e)) from e


@app.get("/progress", dependencies=[Depends(auth)])
def progress(request: Request, course: Course | None = None):
    return {
        "weakest": stats.weakest_topics(course),
        "mastery": stats.mastery_by_topic(course),
        "daily": stats.accuracy_by_day(),
        "spend": stats.spend_by_kind(),
        "queue": request.app.state.queue.stats(),
    }


# built React app, same origin so there's no CORS to deal with. Mount last.
if Path("web/dist").exists():
    app.mount("/", StaticFiles(directory="web/dist", html=True), name="web")
