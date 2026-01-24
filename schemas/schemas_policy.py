# app/schemas.py
from typing import List, Optional
from pydantic import BaseModel

# ---------- POLICY CREATE (NO FILE HERE) ----------

class PolicyCreate(BaseModel):
    title: str
    version: str
    is_general: bool = True
    applicable_roles: List[str] = []

# ---------- ACKNOWLEDGEMENT ----------

class AcknowledgePolicy(BaseModel):
    policy_id: int

   
