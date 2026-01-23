from pydantic import BaseModel, Field
from typing import Optional


class AdminProjectUpdate(BaseModel):
    # ==================================================
    # PROJECT DETAILS (ADMIN ONLY)
    # ==================================================
    project_name: str = Field(
        ...,
        max_length=100,
        description="Project name (required)",
    )

    project_type: Optional[str] = Field(
        None,
        description="Internal / Client / Support / R&D",
    )

    department: Optional[str] = Field(
        None,
        description="Owning department of the project",
    )

    reporting_manager: Optional[str] = Field(
        None,
        description="Reporting manager (emp_code or name)",
    )

    project_details: Optional[str] = Field(
        None,
        description="Additional project description",
    )

    # ==================================================
    # PYDANTIC v2 CONFIG (FIXED)
    # ==================================================
    model_config = {
        "from_attributes": True,
        "str_strip_whitespace": True,
    }
