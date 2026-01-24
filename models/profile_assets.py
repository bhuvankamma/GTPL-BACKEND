from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database_su import Base


class EmployeeAsset(Base):
    __tablename__ = "employee_assets"

    # ==================================================
    # PRIMARY KEY
    # ==================================================
    id = Column(Integer, primary_key=True, index=True)

    # ==================================================
    # EMPLOYEE REFERENCE
    # ==================================================
    emp_code = Column(
        String,
        ForeignKey("employees.emp_code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional ORM relationship
    employee = relationship(
        "Employee",
        backref="assets",
        passive_deletes=True,
    )

    # ==================================================
    # ASSET DETAILS
    # ==================================================
    asset_name = Column(String, nullable=False)
    serial_no = Column(String, unique=True, nullable=True)
    status = Column(String, nullable=True)  # Assigned / Returned / Damaged
    last_audit_date = Column(Date, nullable=True)
