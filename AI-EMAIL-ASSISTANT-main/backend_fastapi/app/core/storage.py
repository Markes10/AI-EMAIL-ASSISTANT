from app.config import settings
from starlette.concurrency import run_in_threadpool
from pathlib import Path
import os


def _has_s3():
    return bool(getattr(settings, 'S3_BUCKET', None))


async def upload_file_path(path: str, key: str = None) -> str:
    """Upload a local file to S3 if configured and return storage URL or local path."""
    if not Path(path).exists():
        raise FileNotFoundError(path)

    if not _has_s3():
        # return local path
        return str(path)

    def _upload():
        import boto3
        s3 = boto3.client('s3')
        bucket = settings.S3_BUCKET
        _key = key or Path(path).name
        with open(path, 'rb') as f:
            s3.put_object(Bucket=bucket, Key=_key, Body=f)
        # construct s3 url
        return f"s3://{bucket}/{_key}"

    return await run_in_threadpool(_upload)


async def upload_bytes(content: bytes, key: str) -> str:
    if not _has_s3():
        # write to uploads folder
        dest = Path(settings.UPLOAD_FOLDER) / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(content)
        return str(dest)

    def _upload():
        import boto3
        s3 = boto3.client('s3')
        bucket = settings.S3_BUCKET
        s3.put_object(Bucket=bucket, Key=key, Body=content)
        return f"s3://{bucket}/{key}"

    return await run_in_threadpool(_upload)
