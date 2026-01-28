from pydantic import BaseModel
from datetime import date
from typing import Optional

class ResignationCreate(BaseModel):
    resignation_date: date
    reason: str
    notice_period_days: int
    requested_lwd: date

class DecisionSchema(BaseModel):
    approve: bool
    reason: Optional[str] = None

class HandoverSchema(BaseModel):
    handover_link: str
    handover_to: str
    pending_tasks: str

class AssetSchema(BaseModel):
    assets_confirmed: bool
    asset_notes: Optional[str] = None

class FinalDocsSchema(BaseModel):
    personal_email: str

class StartOffboardingSchema(BaseModel):
    resignation_date: date
    reason: str
    notice_period_days: int
    requested_lwd: date