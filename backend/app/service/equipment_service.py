from app.common.exceptions import BusinessException
from app.models.equipment import Equipment
from app.common.response import PageResponse
from app.models.lab import Lab
from app.schemas.equipment import (
    EquipmentCreateRequest,
    EquipmentResponse,
    EquipmentUpdateRequest,
)
from sqlalchemy.orm import Session


def get_equipment_page_list(
    page: int,
    page_size: int,
    db: Session,
    keywords: str | None = None,
    lab_id: int | None = None,
):
    query = db.query(Equipment)
    if lab_id is not None:
        query = query.filter(Equipment.lab_id == lab_id)
    if keywords:
        query = query.filter(Equipment.name.ilike(f"%{keywords}%"))
    total = query.count()
    items = (
        query.order_by(Equipment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    result = []
    for item in items:
        res = EquipmentResponse.model_validate(item)
        res.lab_name = item.lab.name if item.lab else None
        result.append(res)

    return PageResponse(list=result, total=total)


def create_equipment(data: EquipmentCreateRequest, db: Session):
    """新增"""
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")

    exist = (
        db.query(Equipment)
        .filter(Equipment.lab_id == data.lab_id, Equipment.name == data.name)
        .first()
    )
    if exist:
        raise BusinessException(message="同一个实验室不能存在同名的设备")

    equipment = Equipment(**data.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return EquipmentResponse.model_validate(equipment)


def update_equipment(equipment_id: int, data: EquipmentUpdateRequest, db: Session):
    """更新"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise BusinessException(message="实验室设备不存在")
    payload = data.model_dump(exclude_none=True)
    # 如果不写这个，是数据库报错，用户看不见
    # 实验室存在性校验
    lab_id = payload.get("lab_id", equipment.lab_id)
    name = payload.get("name", equipment.name)
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")

    # 同实验室设备重名校验
    exist = (
        db.query(Equipment)
        .filter(
            Equipment.lab_id == lab_id,
            Equipment.name == name,
            Equipment.id != equipment_id,
        )
        .first()
    )
    if exist:
        raise BusinessException(message="同一个实验室不能存在同名的设备")

    for field, value in payload.items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return res


def delete_equipment(equipment_id: int, db: Session):
    """删除"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise BusinessException(message="实验室设备不存在")
    db.delete(equipment)
    db.commit()
