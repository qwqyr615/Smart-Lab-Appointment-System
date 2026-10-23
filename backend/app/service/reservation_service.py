from datetime import datetime, time

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest


def create_reservation(db: Session, current_user: User, data: ReservationCreateRequest):
    """创建预约记录"""
    now = datetime.now()
    if data.date < now.date():
        raise BusinessException(message="预约日期不能小于当前的日期")
    if data.end_time <= data.start_time:
        raise BusinessException(message="预约的结束时间必须晚于开始时间")
    current_minute = now.time().replace(second=0, microsecond=0)
    if data.date == now.date() and data.start_time < current_minute:
        raise BusinessException(message="预约开始时间不能小于当前的时间")

    reservation_date = data.date.isoformat()
    start_time = data.start_time.isoformat(timespec="minutes")
    end_time = data.end_time.isoformat(timespec="minutes")

    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭")
    if lab.open_time and data.start_time < time.fromisoformat(lab.open_time):
        raise BusinessException(message="预约时间不能早于实验室的开放时间")
    if lab.close_time and data.end_time > time.fromisoformat(lab.close_time):
        raise BusinessException(message="预约时间不能晚于实验室的关闭时间")

    # 预约实验室设备
    if data.equipment_id is not None:
        equipment = (
            db.query(Equipment)
            .filter(Equipment.id == data.equipment_id)
            .with_for_update()
            .first()
        )
        if not equipment:
            raise BusinessException(message="实验室设备不存在")
        if equipment.status != 1:
            raise BusinessException(message="实验室设备正在维修")
        if equipment.lab_id != data.lab_id:
            raise BusinessException(message="实验室设备不属于该实验室")
        if equipment.quantity < 1:
            raise BusinessException(message="实验室设备数量必须大于0")

    # 实验室或者设备是否是可预约的状态
    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id,
        Reservation.date == reservation_date,
        Reservation.status.in_([0, 1]),  # 0表示待审核  1已通过
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
    )
    if data.equipment_id is not None:
        reservations = (
            query.filter(Reservation.equipment_id == data.equipment_id)
            .with_entities(Reservation.start_time, Reservation.end_time)
            .with_for_update()
            .all()
        )
        # 每条预约占用一台设备；只统计新预约时段内的最大同时占用数。
        events = []
        for reserved_start, reserved_end in reservations:
            events.append((max(reserved_start, start_time), 1))
            events.append((min(reserved_end, end_time), -1))
        occupied = 0
        for _, change in sorted(events):  # 同一时刻先结束再开始
            occupied += change
            if occupied >= equipment.quantity:
                raise BusinessException(message="该时段实验室设备已被预约完")
    else:
        if query.filter(Reservation.equipment_id.is_(None)).first():
            raise BusinessException(message="该时段已预约")

    resvervation_model = Reservation(
        user_id=current_user.id,
        lab_id=data.lab_id,
        equipment_id=data.equipment_id,
        date=reservation_date,
        start_time=start_time,
        end_time=end_time,
        remark=data.remark,
        status=0,
    )
    db.add(resvervation_model)
    db.commit()
