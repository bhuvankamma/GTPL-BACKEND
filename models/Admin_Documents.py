from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy import Integer
from db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    emp_code = Column(String, nullable=False)

    category = Column(String, nullable=False)
    document_type = Column(String)

    file_name = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)

    status = Column(String, nullable=False)        # PENDING / ACCEPTED / REJECTED
    uploaded_by = Column(String, nullable=False)   # ADMIN / EMPLOYEE
    rejection_reason = Column(Text)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
