# /mnt/data/crud.py
import logging
from sqlalchemy.orm import Session
from models.upload_img import UploadTake

logger = logging.getLogger(__name__)

def create_or_update_image(db: Session, emp_code: str, filename: str, content_type: str, data: bytes):
    """
    Legacy: store raw image bytes in DB column `image_data`.
    """
    emp_code = (emp_code or "").strip()
    if not emp_code:
        raise ValueError("emp_code is required")

    obj = db.query(UploadTake).filter(UploadTake.emp_code == emp_code).one_or_none()
    if obj:
        obj.filename = filename
        obj.content_type = content_type
        setattr(obj, "image_data", data)
    else:
        obj = UploadTake(
            emp_code=emp_code,
            filename=filename,
            content_type=content_type,
            image_data=data
        )
        db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def create_or_update(db: Session, emp_code: str, filename: str, content_type: str, s3_key: str):
    """
    Prefered signature (kept for compatibility). If you are not using S3, you can ignore this.
    """
    emp_code = (emp_code or "").strip()
    if not emp_code:
        raise ValueError("emp_code is required")

    obj = db.query(UploadTake).filter(UploadTake.emp_code == emp_code).one_or_none()
    if obj:
        obj.filename = filename
        obj.content_type = content_type
        obj.s3_key = s3_key
    else:
        obj = UploadTake(
            emp_code=emp_code,
            filename=filename,
            content_type=content_type,
            s3_key=s3_key
        )
        db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_image_by_emp_code(db: Session, emp_code: str):
    """
    Defensive getter. Strips whitespace, ensures string input, returns first matching row.
    Uses .first() to avoid MultipleResultsFound errors.
    """
    try:
        if emp_code is None:
            return None
        emp_code = str(emp_code).strip()
        if not emp_code:
            return None
        return db.query(UploadTake).filter(UploadTake.emp_code == emp_code).first()
    except Exception:
        logger.exception("Error fetching emp_code=%r", emp_code)
        raise

def get_by_emp_code(db: Session, emp_code: str):
    return get_image_by_emp_code(db, emp_code)

def delete_image_by_emp_code(db: Session, emp_code: str):
    try:
        if emp_code is None:
            return False
        emp_code = str(emp_code).strip()
        obj = db.query(UploadTake).filter(UploadTake.emp_code == emp_code).first()
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False
    except Exception:
        logger.exception("Error deleting emp_code=%r", emp_code)
        raise

def delete_by_emp_code(db: Session, emp_code: str):
    return delete_image_by_emp_code(db, emp_code)

def list_images(db: Session, limit: int = 100):
    return db.query(UploadTake).order_by(UploadTake.uploaded_at.desc()).limit(limit).all()
