import boto3
import os
from uuid import uuid4

AWS_REGION = "eu-north-1"   # MUST match bucket
S3_BUCKET_NAME = "documentpolicy"
S3_POLICY_FOLDER = "policies"

s3 = boto3.client("s3", region_name=AWS_REGION)


def upload_policy_pdf(*, file_obj, filename: str, policy_id: int, version: str) -> str:
    key = (
        f"{S3_POLICY_FOLDER}/"
        f"policy_{policy_id}/"
        f"v{version}/"
        f"{uuid4()}_{filename}"
    )

    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=S3_BUCKET_NAME,
        Key=key,
        ExtraArgs={
            "ContentType": "application/pdf"
        }
    )

    return key
