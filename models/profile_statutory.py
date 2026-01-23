from sqlalchemy import (
    Column,
    String,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from database_su import Base


class EmployeeStatutory(Base):
    __tablename__ = "employee_statutory"

    # ==================================================
    # EMPLOYEE REFERENCE (PRIMARY KEY)
    # ==================================================
    emp_code = Column(
        String,
        ForeignKey("employees.emp_code", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    # ==================================================
    # BANK DETAILS
    # ==================================================
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)

    # ==================================================
    # STATUTORY DETAILS
    # ==================================================
    pan_number = Column(String, unique=True, index=True)
    aadhaar_number = Column(String, unique=True, index=True)
    epf_uan_ssn = Column(String, unique=True, index=True)
    pf_number = Column(String, nullable=True)
    esi_number = Column(String, nullable=True)

    # ==================================================
    # ORM RELATIONSHIP
    # ==================================================
    employee = relationship(
        "Employee",
        backref="statutory",
        lazy="joined",
    )
