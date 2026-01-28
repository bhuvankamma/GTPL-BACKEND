# app/crud.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid

from models.reimbursement import (
    Reimbursement,
    ReimbursementAttachment
)
from models.empoffboarding import Employee
from models.empoffboarding import Notification
from models.empoffboarding import User

from database_sw import (
    s3_client,
    AWS_S3_BUCKET,
    AWS_S3_REIMBURSEMENT_FOLDER
)

# ==================================================
# CREATE REIMBURSEMENT
# ==================================================
def create_reimbursement(db, data):

    # 1️⃣ Validate employee exists
    employee = (
        db.query(Employee)
        .filter(Employee.emp_code == data.emp_code)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee does not exist"
        )

    # 2️⃣ Get role from USERS table (NOT employees)
    user = (
        db.query(User)
        .filter(User.emp_code == data.emp_code)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User record not found"
        )

    # 3️⃣ Decide flow
    if user.role == "MANAGER":
        status = "PENDING_ADMIN"
        next_level = "ADMIN"
    else:
        status = "PENDING_MANAGER"
        next_level = "MANAGER"

    # 4️⃣ Create reimbursement
    reimbursement = Reimbursement(
        emp_code=data.emp_code,
        expense_type=data.expense_type,
        expense_date=data.expense_date,
        description=data.description,
        amount=data.amount,
        status=status,
        current_level=next_level,
        rejection_reason=None
    )

    db.add(reimbursement)
    db.commit()
    db.refresh(reimbursement)

    return reimbursement


# ==================================================
# UPLOAD ATTACHMENTS
# ==================================================
def upload_files(db: Session, rid: int, files):

    reimbursement = (
        db.query(Reimbursement)
        .filter(Reimbursement.id == rid)
        .first()
    )

    if not reimbursement:
        raise HTTPException(404, "Reimbursement not found")

    for file in files:
        key = f"{AWS_S3_REIMBURSEMENT_FOLDER}/{rid}/{uuid.uuid4()}_{file.filename}"

        s3_client.upload_fileobj(
            file.file,
            AWS_S3_BUCKET,
            key,
            ExtraArgs={"ContentType": file.content_type}
        )

        attachment = ReimbursementAttachment(
            reimbursement_id=rid,
            file_name=file.filename,
            file_path=key
        )

        db.add(attachment)

    db.commit()
    return {"message": "Files uploaded successfully"}


# ==================================================
# UPDATE STATUS (MANAGER / ADMIN)
# ==================================================
def update_status(
    db: Session,
    rid: int,
    status: str,
    next_level: str | None,
    reason: str | None = None,
    sender_role: str | None = None,
    action_by_emp_code: str | None = None
):

    reimbursement = (
        db.query(Reimbursement)
        .filter(Reimbursement.id == rid)
        .first()
    )

    if not reimbursement:
        raise HTTPException(404, "Reimbursement not found")

    # ❌ stop already rejected
    if reimbursement.status.endswith("REJECTED"):
        raise HTTPException(
            status_code=400,
            detail="Rejected reimbursement cannot be processed further"
        )

    # 🔐 Manager must be reporting manager
    if sender_role == "MANAGER":
        employee = (
            db.query(Employee)
            .filter(Employee.emp_code == reimbursement.emp_code)
            .first()
        )

        if not employee:
            raise HTTPException(404, "Employee not found")

        if employee.reporting_manager_emp_code != action_by_emp_code:
            raise HTTPException(
                status_code=403,
                detail="You are not the reporting manager of this employee"
            )

    reimbursement.status = status
    reimbursement.current_level = next_level
    reimbursement.rejection_reason = reason

    message = f"Your reimbursement is {status.replace('_', ' ').title()}"
    if reason:
        message += f". Reason: {reason}"

    create_notification(
        db=db,
        emp_code=reimbursement.emp_code,
        message=message,
        reimbursement_id=rid,
        sender_role=sender_role,
        action=status
    )

    db.commit()
    return {"message": message}


# ==================================================
# CREATE NOTIFICATION
# ==================================================
def create_notification(
    db: Session,
    emp_code: str,
    message: str,
    reimbursement_id: int | None = None,
    sender_role: str | None = None,
    action: str | None = None
):

    notify = Notification(
        emp_code=emp_code,
        message=message,
        reimbursement_id=reimbursement_id,
        sender_role=sender_role,
        action=action
    )

    db.add(notify)
    db.commit()


def get_dashboard_counts(db):
    return {
        "submitted": db.query(Reimbursement).count(),

        "in_progress": db.query(Reimbursement)
        .filter(Reimbursement.status.in_(["PENDING_MANAGER", "PENDING_ADMIN"]))
        .count(),

        "approved": db.query(Reimbursement)
        .filter(Reimbursement.status.in_(["HR_APPROVED", "APPROVED", "APPROVED_AND_PAID"]))
        .count(),

        "blocked": db.query(Reimbursement)
        .filter(Reimbursement.status.in_(["MANAGER_REJECTED", "HR_REJECTED"]))
        .count(),

        "committed": db.query(Reimbursement)
        .filter(Reimbursement.status == "APPROVED_AND_PAID")
        .count(),
    }
