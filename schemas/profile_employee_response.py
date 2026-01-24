from pydantic import BaseModel
from typing import List, Optional
from datetime import date

# ==================================================
# BASIC / PERSONAL INFORMATION
# ==================================================
class EmployeeBasicInfoResponse(BaseModel):
    emp_code: str

    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None

    personal_email: Optional[str] = None
    official_email: Optional[str] = None
    phone: Optional[str] = None

    father_name: Optional[str] = None
    spouse_name: Optional[str] = None
    spouse_dob: Optional[date] = None
    children_names: Optional[str] = None

    vehicle_number: Optional[str] = None
    driving_license_number: Optional[str] = None

    current_address: Optional[str] = None
    permanent_address: Optional[str] = None

    model_config = {"from_attributes": True}


# ==================================================
# BANK & STATUTORY DETAILS
# ==================================================
class EmployeeStatutoryResponse(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None

    pf_number: Optional[str] = None
    epf_uan_ssn: Optional[str] = None
    esi_number: Optional[str] = None
    ppf_number: Optional[str] = None   # ✅ MUST be optional

    model_config = {"from_attributes": True}


# ==================================================
# REPORTING STRUCTURE
# ==================================================
class ReportingResponse(BaseModel):
    manager_emp_code: Optional[str] = None
    level: Optional[int] = None

    model_config = {"from_attributes": True}


# ==================================================
# EMERGENCY CONTACTS
# ==================================================
class EmergencyContactResponse(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    phone: Optional[str] = None
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None

    model_config = {"from_attributes": True}


# ==================================================
# FULL EMPLOYEE PROFILE RESPONSE
# ==================================================
class EmployeeProfileResponse(BaseModel):
    basic_information: EmployeeBasicInfoResponse
    organization_details: EmployeeBasicInfoResponse

    bank_and_statutory: Optional[EmployeeStatutoryResponse] = None

    reporting_management: List[ReportingResponse] = []
    emergency_contacts: List[EmergencyContactResponse] = []

    model_config = {"from_attributes": True}
