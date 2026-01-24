from pydantic import BaseModel, Field
from typing import Optional


class AdminBankStatutoryUpdate(BaseModel):
    # ==================================================
    # BANK DETAILS
    # ==================================================
    bank_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Employee bank name",
    )

    account_number: Optional[str] = Field(
        None,
        max_length=30,
        description="Bank account number",
    )

    ifsc_code: Optional[str] = Field(
        None,
        min_length=11,
        max_length=11,
        description="IFSC code (11 characters)",
    )

    # ==================================================
    # STATUTORY DETAILS
    # ==================================================
    pf_number: Optional[str] = Field(
        None,
        description="Provident Fund number",
    )

    epf_uan_ssn: Optional[str] = Field(
        None,
        description="EPF UAN / SSN number",
    )

    esi_number: Optional[str] = Field(
        None,
        description="ESI number",
    )

    ppf_number: Optional[str] = Field(
        None,
        description="Public Provident Fund number",
    )

    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
from pydantic import BaseModel, Field
from typing import Optional


class AdminBankStatutoryUpdate(BaseModel):
    # ==================================================
    # BANK DETAILS
    # ==================================================
    bank_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Employee bank name",
        example="HDFC Bank",
    )

    account_number: Optional[str] = Field(
        None,
        max_length=30,
        description="Bank account number",
        example="123456789012",
    )

    ifsc_code: Optional[str] = Field(
        None,
        min_length=11,
        max_length=11,
        description="IFSC code (11 characters)",
        example="HDFC0001234",
    )

    # ==================================================
    # STATUTORY DETAILS
    # ==================================================
    pf_number: Optional[str] = Field(
        None,
        description="Provident Fund number",
        example="PF123456789",
    )

    epf_uan_ssn: Optional[str] = Field(
        None,
        description="EPF UAN / SSN number",
        example="100200300400",
    )

    esi_number: Optional[str] = Field(
        None,
        description="ESI number",
        example="ESI998877",
    )

    ppf_number: Optional[str] = Field(
        None,
        description="Public Provident Fund number",
        example="PPF112233",
    )

    # ==================================================
    # PYDANTIC v2 CONFIG
    # ==================================================
    model_config = {
        "from_attributes": True,      # replaces orm_mode
        "str_strip_whitespace": True, # replaces anystr_strip_whitespace
    }
