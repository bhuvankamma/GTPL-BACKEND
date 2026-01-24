from pydantic import BaseModel
from typing import Optional


class ServiceConfigCreate(BaseModel):
    name: str
    type: Optional[str] = "Warranty"
    duration_months: Optional[int] = 0
    price_inr: Optional[int] = 0
    coverage: Optional[str] = None
    sla_response_hours: Optional[int] = 0
    sla_resolution_hours: Optional[int] = 0
    active: Optional[bool] = True


class ServiceConfigBase(BaseModel):
    name: Optional[str]
    type: Optional[str]
    duration_months: Optional[int]
    price_inr: Optional[int]
    coverage: Optional[str]
    sla_response_hours: Optional[int]
    sla_resolution_hours: Optional[int]
    active: Optional[bool]

    
class ServiceConfigImport(ServiceConfigBase):
    id: Optional[int] = None