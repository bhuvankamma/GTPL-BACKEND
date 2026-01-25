from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database_sw import Base

class Reimbursement(Base):
    __tablename__ = "reimbursements"

    id = Column(Integer, primary_key=True, index=True)
    emp_code = Column(String(50), nullable=False)
    expense_type = Column(String(50), nullable=False)
    expense_date = Column(DateTime, nullable=False)
    description = Column(String(255))
    amount = Column(Integer, nullable=False)

    status = Column(String(50), default="PENDING_MANAGER")
    current_level = Column(String(50), default="MANAGER")
    rejection_reason = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ReimbursementAttachment(Base):
    __tablename__ = "reimbursement_attachments"

    id = Column(Integer, primary_key=True, index=True)
    reimbursement_id = Column(
        Integer,
        ForeignKey("reimbursements.id", ondelete="CASCADE"),
        nullable=False
    )
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    emp_code = Column(String(50), nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)

    # optional but recommended
    reimbursement_id = Column(Integer, nullable=True)
    sender_role = Column(String(20), nullable=True)
    action = Column(String(30), nullable=True)

    created_at = Column(DateTime, server_default=func.now())

class Employee(Base):
    __tablename__ = "employees"

    emp_code = Column(String(50), primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    official_email = Column(String(255))
    designation = Column(String(100))
    department = Column(String(100))
    status = Column(String(20))

    # 🔑 THIS IS IMPORTANT
    reporting_manager_emp_code = Column(String(100))

class User(Base):
    __tablename__ = "users"
    emp_code = Column(String, primary_key=True)
    role = Column(String)
