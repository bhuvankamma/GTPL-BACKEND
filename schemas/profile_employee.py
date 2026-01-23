from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date


class EmployeeBasicUpdate(BaseModel):
    # ==================================================
    # PERSONAL DETAILS
    # ==================================================
    first_name: Optional[str] = Field(None, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)

    gender: Optional[str] = Field(
        None,
        description="Male / Female / Other"
    )
    dob: Optional[date] = None
    blood_group: Optional[str] = Field(
        None,
        description="A+, A-, B+, B-, O+, O-, AB+, AB-"
    )

    # ==================================================
    # CONTACT DETAILS (EMPLOYEE EDITABLE)
    # ==================================================
    phone: Optional[str] = Field(
        None,
        min_length=10,
        max_length=15,
        description="Employee phone number"
    )

    personal_email: Optional[EmailStr] = None
    current_address: Optional[str] = None
    permanent_address: Optional[str] = None

    # ==================================================
    # FAMILY DETAILS
    # ==================================================
    father_name: Optional[str] = None
    spouse_name: Optional[str] = None
    spouse_dob: Optional[date] = None
    children_names: Optional[str] = None

    # ==================================================
    # EMERGENCY CONTACT
    # ==================================================
    emergency_contact_name: Optional[str] = None
    emergency_relation: Optional[str] = None
    emergency_mobile: Optional[str] = Field(
        None,
        min_length=10,
        max_length=15,
        description="Emergency contact number"
    )

    # ==================================================
    # IDENTIFICATION (EMPLOYEE-EDITABLE)
    # ==================================================
    vehicle_number: Optional[str] = None
    driving_license_number: Optional[str] = None

    # ==================================================
    # PYDANTIC v2 CONFIG
    # ==================================================
    model_config = {
        "from_attributes": True,
        "str_strip_whitespace": True,
    }
