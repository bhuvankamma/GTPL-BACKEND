

import os

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# ==================================================
# 📤 UPLOAD FILE
# ==================================================
def upload_file(key: str, data: bytes, content_type: str):
    """
    Upload file bytes to S3
    """
    try:
        s3_client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        logger.info(f"Uploaded to S3: {key}")
    except Exception as e:
        logger.error("S3 upload failed", exc_info=e)
        raise

# ==================================================
# 🗑️ DELETE FILE
# ==================================================
def delete_file(key: str):
    """
    Delete file from S3
    """
    try:
        s3_client.delete_object(
            Bucket=AWS_S3_BUCKET,
            Key=key
        )
        logger.info(f"Deleted from S3: {key}")
    except Exception as e:
        logger.error("S3 delete failed", exc_info=e)
        raise

# ==================================================
# 🔗 GENERATE PRESIGNED URL
# ==================================================
def generate_presigned_url(
    key: str,
    expires_in: int = 3600,
    as_attachment: bool = False,
    filename: str | None = None
):
    """
    Generate a presigned GET URL
    """
    try:
        params = {
            "Bucket": AWS_S3_BUCKET,
            "Key": key
        }

        if as_attachment and filename:
            params["ResponseContentDisposition"] = (
                f'attachment; filename="{filename}"'
            )

        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=expires_in
        )

        return url
    except Exception as e:
        logger.error("Presigned URL generation failed", exc_info=e)
        raise
