from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from database_B import (
    get_connection,
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_S3_BUCKET
)
import boto3
import uuid

router = APIRouter(prefix="/upload", tags=["Upload Image"])

# --------------------------------------------------
# S3 CLIENT
# --------------------------------------------------
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

# ==================================================
# POST : UPLOAD IMAGE
# ==================================================
@router.post("/image")
async def upload_image(
    emp_code: str = Form(...),
    file: UploadFile = File(...)
):
    conn = get_connection()
    cur = conn.cursor()

    # 1️⃣ CHECK EMPLOYEE
    cur.execute(
        "SELECT 1 FROM employees WHERE emp_code = %s",
        (emp_code,)
    )
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Employee does not exist")

    # 2️⃣ UPLOAD TO S3
    FOLDER_NAME = "UPLOAD_IMG"

    ext = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    s3_key = f"{FOLDER_NAME}/{new_filename}"

    s3.upload_fileobj(
        file.file,
        AWS_S3_BUCKET,
        s3_key,
        ExtraArgs={"ContentType": file.content_type}
    )

    # 3️⃣ INSERT INTO upload_take (ONLY EXISTING COLUMNS)
    cur.execute(
        """
        INSERT INTO upload_take (
            emp_code,
            filename,
            content_type,
            s3_key
        )
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (
            emp_code,
            file.filename,
            file.content_type,
            s3_key
        )
    )

    upload_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    return {
        "status": "success",
        "upload_id": upload_id,
        "filename": file.filename,
        "s3_key": s3_key
    }

# ==================================================
# GET : FETCH FILES BY EMPLOYEE
# ==================================================
@router.get("/image/{emp_code}")
def get_images(emp_code: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, filename, content_type, s3_key, uploaded_at
        FROM upload_take
        WHERE emp_code = %s
        ORDER BY uploaded_at DESC
        """,
        (emp_code,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No records found")

    return [
        {
            "upload_id": r[0],
            "filename": r[1],
            "content_type": r[2],
            "s3_key": r[3],
            "uploaded_at": r[4],
            "file_url": f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/{r[3]}"
        }
        for r in rows
    ]

# ==================================================
# DELETE : DELETE FILE (DB + S3)
# ==================================================
@router.delete("/image/{upload_id}")
def delete_image(upload_id: int):
    conn = get_connection()
    cur = conn.cursor()

    # 1️⃣ FETCH s3_key
    cur.execute(
        "SELECT s3_key FROM upload_take WHERE id = %s",
        (upload_id,)
    )

    row = cur.fetchone()
    if not row or not row[0]:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="File not found")

    s3_key = row[0]

    # 2️⃣ DELETE FROM S3
    s3.delete_object(
        Bucket=AWS_S3_BUCKET,
        Key=s3_key
    )

    # 3️⃣ DELETE FROM DB
    cur.execute(
        "DELETE FROM upload_take WHERE id = %s",
        (upload_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "status": "success",
        "message": "File deleted successfully"
    }
