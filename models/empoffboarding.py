from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Text,
    Boolean,
    ForeignKey,
    DateTime
)
from sqlalchemy.sql import func
from database_sw import Base

# Existing users table
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    emp_code = Column(String, unique=True, index=True)
    role = Column(String)   # ADMIN / MANAGER / HR / EMPLOYEE
    status = Column(String)

# Existing employees table
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
    date_of_joining = Column(Date)
    
    

# New offboarding table
class OffboardingRequest(Base):
    __tablename__ = "offboardingrequests"

    id = Column(Integer, primary_key=True)
    emp_code = Column(String, ForeignKey("employees.emp_code"))
    manager_emp_code = Column(String)
    hr_emp_code = Column(String, nullable=True)

    initiated_by_role = Column(String)  # ✅ ADD THIS

    status = Column(String, default="DRAFT")

    resignation_date = Column(Date)
    reason = Column(Text)
    notice_period_days = Column(Integer)
    requested_lwd = Column(Date)

    handover_link = Column(String)
    handover_to = Column(String)
    pending_tasks = Column(Text)

    assets_confirmed = Column(Boolean, default=False)
    asset_notes = Column(Text)

    personal_email = Column(String)
    rejection_reason = Column(Text)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    # Who receives the notification
    emp_code = Column(String, index=True)

    # Optional link to offboarding request
    offboarding_request_id = Column(
        Integer,
        ForeignKey("offboardingrequests.id"),
        nullable=True
    )
    title = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    # optional but recommended
    reimbursement_id = Column(Integer, nullable=True)
    sender_role = Column(String(20), nullable=True)
    action = Column(String(30), nullable=True)

    
