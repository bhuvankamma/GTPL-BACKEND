from datetime import date, time
from typing import Optional, Literal
from pydantic import BaseModel, model_validator

# ============================
# COMMON
# ============================

PartialMode = Optional[Literal["full", "half", "custom"]]


class CheckInSchema(BaseModel):
    source: Literal["APP", "DEVICE"]


# ============================
# ATTENDANCE CORRECTION
# ============================

class AttendanceCorrectionRequestSchema(BaseModel):
    attendance_date: date

    correction_type: Literal[
        "MISSING_PUNCH",
        "WRONG_PUNCH",
        "HALF_DAY",
        "WFH"
    ]

    corrected_in: Optional[time] = None   # ✅ TIME ONLY
    corrected_out: Optional[time] = None  # ✅ TIME ONLY

    reason: str

    @model_validator(mode="after")
    def validate_correction(self):
        if self.correction_type == "MISSING_PUNCH":
            if not self.corrected_in:
                raise ValueError("corrected_in is required for Missing Punch")

        elif self.correction_type == "WRONG_PUNCH":
            if not self.corrected_in and not self.corrected_out:
                raise ValueError("At least one corrected time is required")

        elif self.correction_type == "HALF_DAY":
            if not self.corrected_in or not self.corrected_out:
                raise ValueError("Both corrected_in and corrected_out are required")

        elif self.correction_type == "WFH":
            if self.corrected_in or self.corrected_out:
                raise ValueError("WFH should not have corrected times")

        return self

# ============================
# LEAVE
# ============================

class LeaveRequestSchema(BaseModel):
    leave_type_code: Literal["SL", "CL", "AL", "OL"]
    from_date: date
    to_date: date
    partial_mode: Literal["full", "half"] = "full"
    reason: str

    @model_validator(mode="after")
    def validate_leave(self):
        if self.partial_mode == "half" and self.from_date != self.to_date:
            raise ValueError("Half-day leave must be for a single day")
        return self


# ============================
# APPROVAL ACTIONS
# ============================

class ApprovalActionSchema(BaseModel):
    action: Literal["APPROVE", "FINALIZE", "REJECT"]
    reason: Optional[str] = None

    @model_validator(mode="after")
    def validate_reason(self):
        if self.action == "REJECT" and not self.reason:
            raise ValueError("Reason is required when rejecting")
        return self

# ============================
# MANAGER / ADMIN REJECTION
# ============================

class RejectReasonSchema(BaseModel):
    reason: str

# ============================
# TIMESHEET
# ============================

class TimesheetSubmitSchema(BaseModel):
    week_start: date


class TimesheetEditRequestSchema(BaseModel):
    reason: str


# ============================
# OVERTIME
# ============================

class OvertimeCreate(BaseModel):
    date: date
    hours: float
    reason: str

    @model_validator(mode="after")
    def validate_hours(self):
        if self.hours <= 0 or self.hours > 24:
            raise ValueError("Overtime hours must be between 1 and 24")
        return self


class ManagerOvertimeReject(BaseModel):
    reason: str
