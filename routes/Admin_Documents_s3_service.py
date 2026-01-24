import boto3

AWS_REGION = "eu-north-1"
AWS_S3_BUCKET = "gtpl-document"

s3 = boto3.client("s3", region_name=AWS_REGION)

def upload_file(file, key: str):
    s3.upload_fileobj(
        file.file,
        AWS_S3_BUCKET,
        key,
        ExtraArgs={"ContentType": file.content_type}
    )

def generate_signed_url(key: str, expires: int = 3600):
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": AWS_S3_BUCKET, "Key": key},
        ExpiresIn=expires
    )
