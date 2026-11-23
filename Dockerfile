FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/models
WORKDIR /app

# CPU torch wheel: ~200 MB instead of ~2.5 GB of CUDA libs
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir ".[gcp]"

# bake the embedding model in so cold starts don't download it
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

COPY db ./db
COPY web/dist ./web/dist
COPY models ./models

RUN useradd --create-home app && chown -R app /app /models
USER app

EXPOSE 8000
CMD ["uvicorn", "exampilot.api:app", "--host", "0.0.0.0", "--port", "8000"]
