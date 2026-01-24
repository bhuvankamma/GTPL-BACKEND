# app/utils/s3.py
import boto3
import uuid
import os
# ==================================================
# 🔥 AWS S3 CONFIG (ADD HERE)
# ==================================================

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# --------------------------------------------------
# UPLOAD FUNCTION
# --------------------------------------------------
def upload_file_to_s3(
    file_bytes: bytes,
    filename: str,
    folder: str = "service-config-imports"
):
    ext = filename.split(".")[-1].lower()
    folder = "service_warranty"

    key = f"{folder}/{uuid.uuid4()}.{ext}"

    s3.put_object(
        Bucket=AWS_S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType="application/octet-stream",
    )

    return {
        "bucket": AWS_S3_BUCKET,
        "key": key,
        "url": f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}",
    }
