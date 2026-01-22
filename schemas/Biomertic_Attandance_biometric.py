from pydantic import BaseModel
from typing import Literal



class DeviceCreate(BaseModel):
    device_name: str
    device_type: str
    api_endpoint: str
    physical_location: str | None = None
    status: Literal["ACTIVE", "INACTIVE", "MAINTENANCE"] = "ACTIVE"


class DeviceResponse(DeviceCreate):
    id: int

    class Config:
        from_attributes = True
