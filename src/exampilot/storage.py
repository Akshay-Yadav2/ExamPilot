from pathlib import Path

from .config import settings


def save(key: str, data: bytes) -> str:
    if settings.gcs_bucket:
        from google.cloud import storage as gcs

        gcs.Client().bucket(settings.gcs_bucket).blob(key).upload_from_string(data)
        return f"gs://{settings.gcs_bucket}/{key}"

    path = Path(settings.storage_dir) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path)


def load(path: str) -> bytes:
    if path.startswith("gs://"):
        from google.cloud import storage as gcs

        bucket, _, key = path[5:].partition("/")
        return gcs.Client().bucket(bucket).blob(key).download_as_bytes()
    return Path(path).read_bytes()
