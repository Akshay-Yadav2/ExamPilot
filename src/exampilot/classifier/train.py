"""Train the topic head on embeddings that are already in Postgres.

    python -m exampilot.classifier.train data/labels.jsonl
"""

import argparse
import copy
import json
import time
from datetime import date

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .model import TopicNet

IGNORE = -100


def pick_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@torch.no_grad()
def topic_macro_f1(model, X, y_topic, device) -> float:
    from sklearn.metrics import f1_score

    model.eval()
    mask = y_topic != IGNORE
    if not mask.any():
        return 0.0
    _, logits = model(X[mask].to(device))
    pred = logits.argmax(1).cpu().numpy()
    return f1_score(y_topic[mask].numpy(), pred, average="macro")


def train(X: np.ndarray, y_course: np.ndarray, y_topic: np.ndarray,
          train_idx: np.ndarray, val_idx: np.ndarray, n_courses: int, n_topics: int,
          epochs: int = 300, lr: float = 1e-3, weight_decay: float = 1e-2,
          patience: int = 20, seed: int = 0) -> tuple[TopicNet, float]:
    torch.manual_seed(seed)
    device = pick_device()
    X_t = torch.tensor(X, dtype=torch.float32)
    yc = torch.tensor(y_course, dtype=torch.long)
    yt = torch.tensor(y_topic, dtype=torch.long)

    loader = DataLoader(TensorDataset(X_t[train_idx], yc[train_idx], yt[train_idx]),
                        batch_size=64, shuffle=True)
    model = TopicNet(X.shape[1], n_courses, n_topics).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    ce = nn.CrossEntropyLoss(ignore_index=IGNORE)

    best_f1, best_state, bad_epochs = -1.0, None, 0
    for _ in range(epochs):
        model.train()
        for xb, cb, tb in loader:
            xb, cb, tb = xb.to(device), cb.to(device), tb.to(device)
            course_logits, topic_logits = model(xb)
            loss = ce(course_logits, cb)
            # most chunks have no topic label; CE over an all-ignored batch is NaN
            if (tb != IGNORE).any():
                loss = loss + ce(topic_logits, tb)
            opt.zero_grad()
            loss.backward()
            opt.step()

        f1 = topic_macro_f1(model, X_t[val_idx], yt[val_idx], device)
        if f1 > best_f1:
            best_f1, best_state, bad_epochs = f1, copy.deepcopy(model.state_dict()), 0
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                break

    model.load_state_dict(best_state)
    return model.cpu(), best_f1


def baselines(X, y_course, y_topic, train_idx, val_idx, topic_vecs: np.ndarray) -> dict:
    """The numbers TopicNet has to beat."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.neighbors import NearestCentroid

    out = {}
    tr = train_idx[y_topic[train_idx] != IGNORE]
    va = val_idx[y_topic[val_idx] != IGNORE]

    zero_shot = (X[va] @ topic_vecs.T).argmax(1)
    out["zero_shot"] = {"topic_f1": f1_score(y_topic[va], zero_shot, average="macro")}

    for name, clf in [("centroid", NearestCentroid()),
                      ("logreg", LogisticRegression(max_iter=2000))]:
        t0 = time.perf_counter()
        clf.fit(X[tr], y_topic[tr])
        f1 = f1_score(y_topic[va], clf.predict(X[va]), average="macro")
        course_clf = type(clf)(**clf.get_params()).fit(X[train_idx], y_course[train_idx])
        acc = accuracy_score(y_course[val_idx], course_clf.predict(X[val_idx]))
        out[name] = {"topic_f1": f1, "course_acc": acc, "train_s": time.perf_counter() - t0}
    return out


def load_dataset(labels_path: str):
    from psycopg.rows import dict_row

    from ..db import open_pool, pool

    labels = {}
    with open(labels_path) as f:
        for line in f:
            row = json.loads(line)
            if row["topic"]:
                labels[row["chunk_id"]] = row["topic"]

    open_pool()
    with pool.connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        chunks = cur.execute(
            "SELECT id, document_id, course_id, embedding FROM chunks ORDER BY id").fetchall()
        topic_rows = cur.execute("SELECT id, course_id, name FROM topics ORDER BY id").fetchall()
    return chunks, topic_rows, labels


def main() -> None:
    from sklearn.model_selection import GroupShuffleSplit

    from ..config import COURSES, settings
    from ..ingest.embedder import Embedder

    ap = argparse.ArgumentParser()
    ap.add_argument("labels")
    ap.add_argument("--out", default=f"models/topic_head-{date.today().isoformat()}.pt")
    args = ap.parse_args()

    chunks, topic_rows, labels = load_dataset(args.labels)
    courses = list(COURSES)
    topics = [t["id"] for t in topic_rows]
    topic_course = {t["id"]: t["course_id"] for t in topic_rows}

    X = np.stack([np.asarray(c["embedding"], dtype=np.float32) for c in chunks])
    y_course = np.array([courses.index(c["course_id"]) for c in chunks])
    y_topic = np.array([topics.index(labels[c["id"]]) if c["id"] in labels else IGNORE
                        for c in chunks])
    groups = np.array([c["document_id"] for c in chunks])

    # split by document: neighbouring chunks of one deck share too much text
    split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=0)
    train_idx, val_idx = next(split.split(X, groups=groups))

    t0 = time.perf_counter()
    model, best_f1 = train(X, y_course, y_topic, train_idx, val_idx, len(courses), len(topics))
    train_s = time.perf_counter() - t0

    embedder = Embedder(settings.embed_model)
    topic_vecs = embedder.encode([t["name"] for t in topic_rows])
    report = baselines(X, y_course, y_topic, train_idx, val_idx, topic_vecs)
    report["topicnet"] = {"topic_f1": best_f1, "train_s": train_s}

    print(f"{'model':<10} {'topic F1':>9} {'course acc':>11} {'train s':>8}")
    for name, m in report.items():
        print(f"{name:<10} {m['topic_f1']:>9.3f} {m.get('course_acc', float('nan')):>11.3f} "
              f"{m.get('train_s', 0):>8.1f}")

    torch.save({
        "state_dict": model.state_dict(),
        "courses": courses,
        "topics": topics,
        "topic_course": topic_course,
        "embed_model": settings.embed_model,
        "dim": X.shape[1],
        "metrics": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in report.items()},
    }, args.out)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
