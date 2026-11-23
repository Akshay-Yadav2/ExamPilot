import os
from dataclasses import dataclass


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    database_url: str = _env(
        "DATABASE_URL", "postgresql://exampilot:exampilot@localhost:5432/exampilot"
    )
    redis_url: str = _env("REDIS_URL", "redis://localhost:6379/0")
    model: str = _env("EXAMPILOT_MODEL", "claude-opus-5-5")
    embed_model: str = _env("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
    storage_dir: str = _env("STORAGE_DIR", "./data/uploads")
    gcs_bucket: str = _env("GCS_BUCKET")
    api_token: str = _env("EXAMPILOT_TOKEN")
    classifier_path: str = _env("CLASSIFIER_PATH", "./models/topic_head.pt")


settings = Settings()
COURSES = ("daa", "swe", "ai")
