from sqlalchemy.orm import Session
from sqlalchemy import func, text
from fastapi import HTTPException

from models.empoffboarding import Employee, User, OffboardingRequest
from utils.notifications import create_notification


# ==================================================
# EMPLOYEE START OFFBOARDING
# ==================================================
def employee_start_offboarding(db: Session, emp_code: str, manager_emp_code: str, data):

    employee = db.query(Employee).filter(
        Employee.emp_code == emp_code,
        func.lower(Employee.status) == "active"
    ).first()

    if not employee:
        raise HTTPException(404, "Employee not found or inactive")
    
    if employee.reporting_manager_emp_code != manager_emp_code:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to choose this manager"
        )


    manager = db.query(User).filter(
        User.emp_code == manager_emp_code,
        User.role == "MANAGER",
        func.lower(User.status) == "active"
    ).first()
    if not manager:

        raise HTTPException(403, "Invalid reporting manager")

    req = OffboardingRequest(
        emp_code=emp_code,
        manager_emp_code=manager_emp_code,
        status="MANAGER_PENDING",
        resignation_date=data.resignation_date,
        reason=data.reason,
        notice_period_days=data.notice_period_days,
        requested_lwd=data.requested_lwd
    )

    db.add(req)
    db.commit()
    db.refresh(req)

    create_notification(
        db,
        emp_code=manager_emp_code,
        message=f"{emp_code} submitted resignation for your approval",
        sender_role="EMPLOYEE",
        action="MANAGER_PENDING"
    )

    db.commit()
    db.refresh(req)

    return {
        "success": True,
        "message": "Offboarding request submitted successfully",
        "request_id": req.id,
        "status": req.status
    }


# ==================================================
# MANAGER START OFFBOARDING (HR APPROVAL)
# ==================================================
def manager_start_offboarding(db: Session, manager_emp_code: str, data):

    manager = db.query(Employee).filter(
        Employee.emp_code == manager_emp_code,
        func.lower(Employee.status) == "active"
    ).first()

    if not manager:
        raise HTTPException(404, "Manager not found or inactive")

    manager_user = db.query(User).filter(
        User.emp_code == manager_emp_code,
        User.role == "MANAGER",
        func.lower(User.status) == "active"
    ).first()

    if not manager_user:
        raise HTTPException(403, "Only MANAGER can start this offboarding")

    req = OffboardingRequest(
        emp_code=manager_emp_code,
        manager_emp_code=manager_emp_code,   # NOT NULL
        initiated_by_role="MANAGER",
        status="HR_PENDING",
        resignation_date=data.resignation_date,
        reason=data.reason,
        notice_period_days=data.notice_period_days,
        requested_lwd=data.requested_lwd
    )

    db.add(req)
    db.commit()
    db.refresh(req)

    hr_users = (
        db.query(User)
        .join(Employee, Employee.emp_code == User.emp_code)
        .filter(
            User.role.in_(["HR", "ADMIN"]),
            func.lower(User.status) == "active",
            func.lower(Employee.status) == "active"
        )
        .all()
    )

    for hr in hr_users:
        create_notification(
            db=db,
            emp_code=hr.emp_code,  # ✅ SAFE (FK guaranteed)
            message=f"Manager {manager_emp_code} submitted resignation for approval",
            sender_role="MANAGER",
            action="HR_PENDING"
        )

    db.commit()

    return {
        "message": "Manager offboarding initiated successfully",
        "request_id": req.id,
        "status": req.status
    }


# ==================================================
# MANAGER DECISION (EMPLOYEE FLOW)
# ==================================================
def manager_decision(db: Session, req_id: int, manager_emp_code: str, approve: bool, reason: str | None):

    req = db.query(OffboardingRequest).filter(
        OffboardingRequest.id == req_id
    ).first()

    if not req:
        raise HTTPException(404, "Request not found")

    if req.manager_emp_code != manager_emp_code:
        raise HTTPException(403, "Unauthorized")

    if approve:
        req.status = "MANAGER_APPROVED"
        message = "Your resignation was approved by manager"
        action = "MANAGER_APPROVED"
    else:
        req.status = "MANAGER_REJECTED"
        req.rejection_reason = reason
        message = f"Resignation rejected by manager. Reason: {reason}"
        action = "MANAGER_REJECTED"

    db.commit()

    create_notification(
        db,
        emp_code=req.emp_code,
        message=message,
        sender_role="MANAGER",
        action=action
    )

    db.commit()
    return {
        "success": True,
        "request_id": req.id,
        "status": req.status
    }


# ==================================================
# HANDOVER (EMPLOYEE)
# ==================================================
def save_handover(db: Session, req_id: int, emp_code: str, data):

    req = db.get(OffboardingRequest, req_id)

    if not req:
        raise HTTPException(404, "Request not found")

    # Allow employee OR manager
    if emp_code not in [req.emp_code, req.manager_emp_code]:
        raise HTTPException(403, "Unauthorized")

    # Allow if ANY one approval exists
    if req.status not in ["MANAGER_APPROVED", "HR_APPROVED"]:
        raise HTTPException(409, "Approval required")

    req.handover_link = data.handover_link
    req.handover_to = data.handover_to
    req.pending_tasks = data.pending_tasks
    req.status = "HANDOVER_COMPLETED"

    db.commit()
    return {
        "success": True,
        "message": "Handover completed successfully"
    }



# ==================================================
# ASSETS CONFIRMATION
# ==================================================
def confirm_assets(db: Session, req_id: int, emp_code: str, data):

    req = db.get(OffboardingRequest, req_id)

    if not req:
        raise HTTPException(404, "Request not found")

    if emp_code not in [req.emp_code, req.manager_emp_code]:
        raise HTTPException(403, "Unauthorized")

    if req.status != "HANDOVER_COMPLETED":
        raise HTTPException(409, "Handover not completed")

    req.assets_confirmed = True
    req.asset_notes = data.asset_notes
    req.status = "ASSETS_CONFIRMED"

    db.commit()
    return {
        "success": True,
        "message": "Assets confirmed successfully"
    }



# ==================================================
# FINAL DOCS
# ==================================================
def submit_final_docs(db: Session, req_id: int, emp_code: str, email: str):

    req = db.get(OffboardingRequest, req_id)

    if not req:
        raise HTTPException(404, "Request not found")

    if emp_code not in [req.emp_code, req.manager_emp_code]:
        raise HTTPException(403, "Unauthorized")

    if req.status != "ASSETS_CONFIRMED":
        raise HTTPException(409, "Assets not confirmed")

    req.personal_email = email
    req.status = "SUBMITTED_TO_HR"

    db.commit()
    return {
        "success": True,
        "message": "Final documents submitted"
    }



# ==================================================
# HR / ADMIN FINAL DECISION
# ==================================================
def hr_decision(
    db: Session,
    req_id: int,
    hr_emp_code: str,
    approve: bool,
    reason: str | None
):
    req = db.query(OffboardingRequest).filter(
        OffboardingRequest.id == req_id
    ).first()

    if not req:
        raise HTTPException(404, "Request not found")
    



    # HR / ADMIN validation
    hr_user = db.query(User).filter(
        User.emp_code == hr_emp_code,
        User.role.in_(["HR", "ADMIN"]),
        func.lower(User.status) == "active"
    ).first()

    if not hr_user:
        raise HTTPException(403, "HR / ADMIN access required")

    # 🔹 FIRST HR DECISION (Manager-start flow)
    
    if approve:
            req.status = "HR_APPROVED"
    else:
        req.status = "HR_REJECTED"
        req.rejection_reason = reason

    # 🔹 FINAL HR DECISION
    req.hr_emp_code == hr_emp_code
    db.commit()

    # 🔔 Notification
    create_notification(
        db=db,
        emp_code=req.emp_code,
        message=f"HR {'approved' if approve else 'rejected'} your request",
        sender_role="HR",
        action=req.status
    )


    return {
        "message": "HR decision recorded",
        "request_id": req.id,
        "status": req.status
    }


def hr_finalize_exit(
    db: Session,
    req_id: int,
    hr_emp_code: str
):
    req = db.query(OffboardingRequest).filter(
        OffboardingRequest.id == req_id
    ).first()

    if not req:
        raise HTTPException(404, "Request not found")

    if req.status != "SUBMITTED_TO_HR":
        raise HTTPException(
            409,
            "Final documents not submitted"
        )

    # Mark request completed
    req.status = "EXIT_COMPLETED"

    # Mark employee inactive
    employee = db.query(Employee).filter(
        Employee.emp_code == req.emp_code
    ).first()

    if employee:
        employee.status = "INACTIVE"

    # Mark user inactive
    user = db.query(User).filter(
        User.emp_code == req.emp_code
    ).first()

    if user:
        user.status = "INACTIVE"

    db.commit()

    create_notification(
        db,
        emp_code=req.emp_code,
        message="Your exit process has been completed by HR",
        sender_role="HR",
        action="EXIT_COMPLETED"
    )

    return {
        "message": "Exit completed successfully",
        "status": "EXIT_COMPLETED"
    }

