from sqlalchemy import (
    Column,
    String,
    Date,
    Text,
    Boolean,
    Integer,
    Numeric,
)
from sqlalchemy.dialects.postgresql import JSONB
from database_su import Base


class Employee(Base):
    __tablename__ = "employees"

    emp_code = Column(String, primary_key=True, index=True)

    # -------- Basic --------
    first_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    blood_group = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    father_name = Column(String, nullable=True)

    # -------- Contact --------
    phone = Column(String, nullable=True)
    personal_email = Column(String, nullable=True)
    official_email = Column(String, nullable=True)
    profile_photo = Column(String, nullable=True)
    current_address = Column(Text, nullable=True)
    permanent_address = Column(Text, nullable=True)

    # -------- Employment --------
    employment_type = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    department = Column(String, nullable=True)
    department_id = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    reporting_manager_emp_code = Column(String, nullable=True)
    managers_user_id = Column(Integer, nullable=True)
    grade_level = Column(String, nullable=True)
    primary_project_code = Column(String, nullable=True)
    date_of_joining = Column(Date, nullable=True)
    status = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # -------- Payroll (FIXED) --------
    basic_salary = Column(Numeric(12, 2), nullable=True)
    allowances = Column(JSONB, nullable=True)          # ✅ FIX IS HERE
    variable_pay_percent = Column(Numeric(5, 2), nullable=True)

    # -------- Family --------
    marriage_date = Column(Date, nullable=True)
    spouse_name = Column(String, nullable=True)
    spouse_dob = Column(Date, nullable=True)
    children_names = Column(Text, nullable=True)
    children_dobs = Column(Text, nullable=True)

    # -------- Statutory --------
    aadhaar_ssn = Column(String, nullable=True)
    insurance_number = Column(String, nullable=True)

    # -------- Assets --------
    vehicle_number = Column(String, nullable=True)
    driving_license_number = Column(String, nullable=True)

    # -------- Exit --------
    resignation_date = Column(Date, nullable=True)
    resignation_reason = Column(Text, nullable=True)
    last_working_day = Column(Date, nullable=True)
    termination_action = Column(String, nullable=True)
    actual_termination_date = Column(Date, nullable=True)

    # -------- System --------
    password = Column(String, nullable=True)
    updated_at = Column(Date, nullable=True)
