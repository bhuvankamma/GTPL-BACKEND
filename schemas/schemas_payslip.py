# app/schemas.py
from pydantic import BaseModel
from typing import Optional, List

class SelectTaxRegime(BaseModel):
    tax_regime: str
    financial_year: str

class GeneratePayslip(BaseModel):
    emp_code: str
    month: str
    year: int

class BulkGenerate(BaseModel):
    month: str
    year: int
    emp_codes: Optional[List[str]] = None

class Form16Request(BaseModel):
    emp_code: str
    financial_year: str
