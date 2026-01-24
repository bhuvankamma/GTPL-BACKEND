# app/utils.py

from fastapi import HTTPException

# Allowed MIME types for upload
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png"
}

def validate_file(file, max_upload_mb: int):
    """
    Validate uploaded file type and size
    """

    # 1️⃣ Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}"
        )

    # 2️⃣ Validate file size
    file.file.seek(0, 2)  # move to end
    file_size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)     # reset pointer

    if file_size_mb > max_upload_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {max_upload_mb} MB limit"
        )
