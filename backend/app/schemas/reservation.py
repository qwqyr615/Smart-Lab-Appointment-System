import re
from datetime import date as Date, time as Time

from pydantic import BaseModel, field_validator, ConfigDict


class ReservationCreateRequest(BaseModel):
    lab_id: int
    equipment_id: int | None = None
    date: Date
    start_time: Time
    end_time: Time
    remark: str | None = None

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, value):
        if not isinstance(value, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value
        ):
            raise ValueError("预约日期格式应为 YYYY-MM-DD")
        return value

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def validate_time_format(cls, value):
        if not isinstance(value, str) or not re.fullmatch(r"[0-9]{2}:[0-9]{2}", value):
            raise ValueError("预约时间格式应为 HH:mm")
        return value


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    lab_id: int
    lab_name: str | None = None
    equipment_id: int | None = None
    equipment_name: str | None = None
    type: str | None = None
    date: str
    start_time: str
    end_time: str
    remark: str | None = None
    status: int

    model_config = ConfigDict(from_attributes=True)


class AuditReservationRequest(BaseModel):
    status: int  #  1 | 2
