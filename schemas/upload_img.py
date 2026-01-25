# app/schemas.py
from pydantic import BaseModel
from datetime import datetime

class ImageOut(BaseModel):
    emp_code: str
    filename: str | None = None
    content_type: str | None = None

    # NEW — for Lambda/S3 storage
    s3_key: str | None = None

    uploaded_at: datetime | None = None

    class Config:
        orm_mode = True

