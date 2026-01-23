import base64
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from database_B import get_db_conn
from models.s3_form12bb import (
    upload_file,
    delete_file,
    generate_presigned_url,
    AWS_S3_BUCKET
)
from schemas.templates_form12bb import render_form12bb
from models.config_form12bb import DEFAULT_USER_ID, MAX_UPLOAD_MB
from utils.form12bb import validate_file

router = APIRouter(prefix="/form12bb", tags=["Form12BB"])


# ==================================================
# GET : TEMPLATE PDF (BASE64 STORED)
# ==================================================


@router.get("/template/")
def get_template():
    from models.config_form12bb import TEMPLATE_PDF_BASE64

    if not TEMPLATE_PDF_BASE64:
        raise HTTPException(status_code=404, detail="Template not available")

    return Response(
        base64.b64decode(TEMPLATE_PDF_BASE64),
        media_type="application/pdf"
    )

# ==================================================
# GET : VIEW FORM12BB PAGE
# ==================================================
@router.get("/view", response_class=HTMLResponse)
def view_form12bb(fy: str):
    html = f"""
    <!doctype html>
    <html>
    <head>
        <title>Form 12BB</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
            }}
            iframe {{
                width: 100%;
                height: 100vh;
                border: none;
            }}
        </style>
    </head>
    <body>
        <iframe src="/form12bb/template"></iframe>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# ==================================================
# POST : UPLOAD FORM12BB FILE
# ==================================================
@router.post("/upload")
async def upload_form12bb(
    emp_code: str = Form(...),
    fy: str = Form(...),
    file: UploadFile = File(...)
):
    validate_file(file, MAX_UPLOAD_MB)
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM employees WHERE emp_code = %s",
        (emp_code,)
    )

    if not cur.fetchone():
        raise HTTPException(
            status_code=400,
            detail="Invalid emp_code"
        )

    key = (
        f"form12bb/{emp_code}/{fy}/"
        f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    )

    data = await file.read()
    upload_file(key, data, file.content_type)

    file_url = f"s3://{AWS_S3_BUCKET}/{key}"

    conn = get_db_conn()
    try:
        cur = conn.cursor()

        # 🔥 THIS IS THE IMPORTANT PART
        cur.execute(
            """
            INSERT INTO form12bb_uploads
            (user_id,emp_code, financial_year, filename, filepath, file_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                DEFAULT_USER_ID,
                emp_code,
                fy,
                file.filename,
                key,
                file_url
            )
        )

        upload_id = cur.fetchone()[0]   # 🔥 FETCH GENERATED ID
        conn.commit()

    except Exception as e:
        print("🔥 DB ERROR:", e)   # <-- ADD THIS
        delete_file(key)
        raise HTTPException(
            status_code=500,
            detail=str(e)          # <-- SHOW REAL ERROR
        )
    finally:
        conn.close()

    # 🔥 RETURN THE ID
    return {
        "status": "success",
        "upload_id": upload_id,
        "emp_code": emp_code,
        "filename": file.filename
    }

# ==================================================
# GET : DOWNLOAD FILE (ATTACHMENT)
# ==================================================
@router.get("/download/{upload_id}/")
def download_file(upload_id: int):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT filename, filepath
            FROM form12bb_uploads
            WHERE id = %s
            """,
            (upload_id,)
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        filename, filepath = row
        url = generate_presigned_url(
            key=filepath,
            as_attachment=True,
            filename=filename
        )
        return RedirectResponse(url)
    finally:
        conn.close()

# ==================================================
# GET : VIEW FILE INLINE
# ==================================================
@router.get("/view/{upload_id}/")
def view_inline(upload_id: int):
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT filepath
            FROM form12bb_uploads
            WHERE id = %s
            """,
            (upload_id,)
        )
        row = cur.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="File not found")

        url = generate_presigned_url(key=row[0])
        return RedirectResponse(url)
    finally:
        conn.close()
