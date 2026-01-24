from fastapi import APIRouter, HTTPException, Request,UploadFile,File
from fastapi.encoders import jsonable_encoder
from crud import service_config_sNw as crud
import json
from schemas.schemas_sNw import ServiceConfigCreate
# import pandas as pd
# from PyPDF2 import PdfReader
from fastapi import UploadFile, File, HTTPException
from io import BytesIO
from utils.s3_sNw import upload_file_to_s3
from fastapi.responses import StreamingResponse,Response
from datetime import datetime
from utils.s3_sNw import upload_file_to_s3



router = APIRouter(prefix="/configs", tags=["Service Configs"])

# ---------------- FIX: STATIC ROUTES FIRST ----------------

@router.get("/export/json")
def export_configs_json():
    data = crud.export_configs()

    return Response(
        json.dumps(data, indent=2, default=str),
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=service_configs.json"
        },
    )


@router.post("/import/file")
async def import_configs_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".json", ".xlsx", ".xls", ".pdf")):
        raise HTTPException(
            status_code=400,
            detail="Only JSON, Excel, and PDF files are supported",
        )

    file_bytes = await file.read()

    s3_info = upload_file_to_s3(
        file_bytes=file_bytes,
        filename=file.filename,
    )

    return {
        "message": "File uploaded successfully",
        "file": s3_info,
    }

    # ---------- VALIDATION ----------
    if not isinstance(records, list):
        raise HTTPException(400, "Invalid file structure")

    # ---------- IMPORT ----------
    return jsonable_encoder(
        crud.import_configs(records)
    )

    # ---------- VALIDATION ----------
    if not isinstance(records, list):
        raise HTTPException(400, "Invalid file structure")

    # ---------- IMPORT ----------
    return jsonable_encoder(
        crud.import_configs(records)
    )


@router.get("/")
def list_configs(request: Request):
    return jsonable_encoder(
        crud.list_configs(dict(request.query_params))
    )


@router.post("/")
def create_config(payload: ServiceConfigCreate):
    return jsonable_encoder(
        crud.create_config(payload.dict())
    )


# ---------------- DYNAMIC ROUTES LAST ----------------

@router.get("/{id}")
def get_config(id: int):
    row = crud.get_config(id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return jsonable_encoder(row)


@router.put("/{id}")
def update_config(id: int, payload: ServiceConfigCreate):
    return jsonable_encoder(
        crud.update_config(id, payload.dict())
    )


@router.delete("/{id}")
def delete_config(id: int):
    return jsonable_encoder(
        crud.delete_config(id)
    )


@router.post("/{id}/toggle")
def toggle_active(id: int):
    row = crud.toggle_active(id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return jsonable_encoder(row)
