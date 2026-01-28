from sqlalchemy import text
from sqlalchemy.orm import Session


def create_notification(
    db: Session,
    emp_code: str,
    message: str,
    sender_role: str,
    action: str,
):
    db.execute(
        text("""
            INSERT INTO notifications
            (emp_code, message, is_read, sender_role, action)
            VALUES (:emp_code, :message, false, :sender_role, :action)
        """),
        {
            "emp_code": emp_code,
            "message": message,
            "sender_role": sender_role,
            "action": action,
        }
    )
