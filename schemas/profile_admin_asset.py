from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class AdminAssetUpdate(BaseModel):
    # ==================================================
    # ASSET DETAILS (ADMIN ONLY)
    # ==================================================
    asset_name: str = Field(
        ...,
        max_length=100,
        description="Name of the asset (Laptop, ID Card, Mobile, etc.)",
        example="Laptop",
    )

    serial_no: Optional[str] = Field(
        None,
        max_length=100,
        description="Unique serial number of the asset",
        example="DLX-9384-XY",
    )

    status: Optional[str] = Field(
        None,
        description="Assigned / Returned / Damaged / Lost",
        example="Assigned",
    )

    last_audit_date: Optional[date] = Field(
        None,
        description="Last audit date of the asset",
        example="2024-12-01",
    )

    # ==================================================
    # PYDANTIC v2 CONFIG
    # ==================================================
    model_config = {
        "from_attributes": True,      # replaces orm_mode
        "str_strip_whitespace": True, # replaces anystr_strip_whitespace
    }
