import boto3
from botocore.exceptions import ClientError
import os
from uuid import uuid4

BUCKET_NAME = "documentshr"

s3 = boto3.client("s3")


def upload_file_to_s3(local_path: str, folder: str) -> str:
    """
    Uploads a file to S3 and returns public URL
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError("File not found")

    filename = f"{folder}/{uuid4()}_{os.path.basename(local_path)}"

    try:
        s3.upload_file(
            local_path,
            BUCKET_NAME,
            filename,
            ExtraArgs={"ACL": "private"}
        )
    except ClientError as e:
        raise Exception(f"S3 upload failed: {e}")

    return f"s3://{BUCKET_NAME}/{filename}"
