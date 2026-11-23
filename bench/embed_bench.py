"""Embedding throughput: CPU vs Apple MPS vs CUDA, batch sizes, fp16.

    python bench/embed_bench.py chunks.jsonl mps
"""

import json
import sys
import time
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

MODEL = "BAAI/bge-small-en-v1.5"
BATCHES = [8, 16, 32, 64, 128, 256]


def sync(device: str) -> None:
    # GPU calls are async; without this you're timing the launch
    if device == "cuda":
        torch.cuda.synchronize()
    elif device == "mps":
        torch.mps.synchronize()


def bench(device: str, dtype: str, texts: list[str], batch_sizes: list[int], repeats: int = 3):
    model = SentenceTransformer(MODEL, device=device)
    if dtype == "fp16":
        model = model.half()
    rows = []
    for bs in batch_sizes:
        model.encode(texts[: bs * 4], batch_size=bs)  # warm-up
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(repeats):
            sync(device)
            t0 = time.perf_counter()
            model.encode(texts, batch_size=bs, normalize_embeddings=True)
            sync(device)
            times.append(time.perf_counter() - t0)
        rows.append({
            "device": device,
            "dtype": dtype,
            "batch_size": bs,
            "chunks_per_s": round(len(texts) / min(times), 1),
            "peak_mb": round(torch.cuda.max_memory_allocated() / 2**20) if device == "cuda" else None,
        })
        print(rows[-1], flush=True)
    return rows


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        texts = [json.loads(line)["text"] for line in f]
    device = sys.argv[2]
    dtypes = ["fp32", "fp16"] if device == "cuda" else ["fp32"]
    results = [r for dt in dtypes for r in bench(device, dt, texts, BATCHES)]
    out = Path("bench/results") / f"{device}.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"wrote {out}")
