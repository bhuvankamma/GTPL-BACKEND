from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date


class AdminEmployeeBasicUpdate(BaseModel):
    # ==================================================
    # PERSONAL DETAILS
    # ==================================================
    first_name: Optional[str] = Field(None, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    gender: Optional[str]
    dob: Optional[date]
    blood_group: Optional[str]
    nationality: Optional[str]

    # ==================================================
    # EMPLOYMENT DETAILS (ADMIN ONLY)
    # ==================================================
    employment_type: Optional[str]
    date_of_joining: Optional[date]
    status: Optional[str]

    # ==================================================
    # EMAILS
    # ==================================================
    official_email: Optional[EmailStr]
    personal_email: Optional[EmailStr]

    # ==================================================
    # FAMILY & EMERGENCY
    # ==================================================
    father_name: Optional[str]
    spouse_name: Optional[str]
    spouse_dob: Optional[date]
    children_names: Optional[str]

    emergency_contact_name: Optional[str]
    emergency_relation: Optional[str]
    emergency_mobile: Optional[str]

    # ==================================================
    # KYC & ADDRESS
    # ==================================================
    pan_number: Optional[str]
    aadhaar_number: Optional[str]
    vehicle_number: Optional[str]
    driving_license_number: Optional[str]

    current_address: Optional[str]
    permanent_address: Optional[str]

    # ==================================================
    # ORGANIZATION STRUCTURE
    # ==================================================
    legal_entity: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    grade_level: Optional[str]
    location: Optional[str]

    reporting_manager_emp_code: Optional[str]
    primary_project_code: Optional[str]
    group_doj: Optional[date]

    # ==================================================
    # EXIT / TERMINATION
    # ==================================================
    resignation_date: Optional[date]
    last_working_day: Optional[date]
    resignation_reason: Optional[str]
    termination_action: Optional[str]
    actual_termination_date: Optional[date]

    # ==================================================
    # PYDANTIC v2 CONFIG (FIX)
    # ==================================================
    model_config = {
        "from_attributes": True,      # replaces orm_mode
        "str_strip_whitespace": True, # replaces anystr_strip_whitespace
    }
