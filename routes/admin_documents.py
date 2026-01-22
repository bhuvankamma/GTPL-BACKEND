from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from db import get_db
from models import Admin_Documents
from routes.Admin_Documents_s3_service import upload_file, generate_signed_url

router = APIRouter(prefix="/admin", tags=["Admin Documents"])

# =====================================================
# 1️⃣ ADMIN OWN DOCUMENTS
# =====================================================

@router.post("/documents")
def upload_admin_document(
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    s3_key = f"admin/{uuid4()}_{file.filename}"
    upload_file(file, s3_key)

    doc = Document(
        emp_code="ADMIN",
        category=category,
        document_type="ADMIN_DOC",
        file_name=file.filename,
        s3_key=s3_key,
        status="ACCEPTED",
        uploaded_by="ADMIN"
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "message": "Admin document uploaded",
        "document_id": doc.id
    }


@router.get("/documents")
def list_admin_documents(
    category: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(
        Document.emp_code == "ADMIN",
        Document.is_active == True
    )

    if category:
        query = query.filter(Document.category == category)

    return query.all()


@router.delete("/documents/{doc_id}")
def delete_admin_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    doc.is_active = False
    db.commit()
    return {"message": "Admin document deleted"}

# =====================================================
# 2️⃣ ADMIN → EMPLOYEE DOCUMENTS
# =====================================================

@router.get("/employees/{emp_code}/documents")
def list_employee_documents(
    emp_code: str,
    category: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Document).filter(
        Document.emp_code == emp_code,
        Document.is_active == True
    )

    if category:
        query = query.filter(Document.category == category)

    return query.all()


@router.post("/employees/{emp_code}/documents")
def upload_document_for_employee(
    emp_code: str,
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    s3_key = f"employees/{emp_code}/{uuid4()}_{file.filename}"
    upload_file(file, s3_key)

    doc = Document(
        emp_code=emp_code,
        category=category,
        document_type="ADMIN_UPLOADED",
        file_name=file.filename,
        s3_key=s3_key,
        status="ACCEPTED",
        uploaded_by="ADMIN"
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "message": "Document uploaded for employee",
        "document_id": doc.id
    }


@router.patch("/employees/{emp_code}/documents/{doc_id}/status")
def accept_reject_employee_document(
    emp_code: str,
    doc_id: int,
    status: str = Form(...),
    rejection_reason: str | None = Form(None),
    db: Session = Depends(get_db)
):
    if status not in ["ACCEPTED", "REJECTED"]:
        raise HTTPException(400, "Invalid status")

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.emp_code == emp_code,
        Document.uploaded_by == "EMPLOYEE",
        Document.is_active == True
    ).first()

    if not doc:
        raise HTTPException(404, "Document not found")

    if status == "REJECTED":
        if not rejection_reason:
            raise HTTPException(
                400, "Rejection reason is required when rejecting a document"
            )
        doc.rejection_reason = rejection_reason
    else:
        doc.rejection_reason = None  # clear old reason if accepted later

    doc.status = status
    db.commit()

    return {"message": f"Document {status.lower()}"}



@router.get("/employees/{emp_code}/documents/{doc_id}/download")
def admin_download_employee_doc(
    emp_code: str,
    doc_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.emp_code == emp_code,
        Document.uploaded_by == "EMPLOYEE",
        Document.is_active == True
    ).first()


    if not doc:
        raise HTTPException(404, "Document not found")

    return {"download_url": generate_signed_url(doc.s3_key)}
