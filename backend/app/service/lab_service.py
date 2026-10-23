from sqlalchemy import or_
from app.common.exceptions import BusinessException
from app.models.lab import Lab
from app.common.response import PageResponse
from app.schemas.lab import (
    LabCreateRequest,
    LabResponse,
    LabUpdateRequest,
)
from sqlalchemy.orm import Session


def get_lab_page_list(
    page: int,
    page_size: int,
    db: Session,
    keywords: str | None = None,
    status: int | None = None,
):
    query = db.query(Lab)
    if keywords:
        query = query.filter(
            or_(Lab.name.ilike(f"%{keywords}%"), Lab.location.ilike(f"%{keywords}%"))
        )
    if status is not None:
        query = query.filter(Lab.status == status)
    total = query.count()
    items = (
        query.order_by(Lab.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PageResponse(
        list=[LabResponse.model_validate(item) for item in items], total=total
    )


def get_lab(lab_id: int, db: Session, status: int | None = None):
    query = db.query(Lab).filter(Lab.id == lab_id)
    if status is not None:
        query = query.filter(Lab.status == status)
    lab = query.first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    return LabResponse.model_validate(lab)


"""管理员增删改查试验室"""


def create_lab(data: LabCreateRequest, db: Session):
    """新增实验室"""
    exist = db.query(Lab).filter(Lab.name == data.name).first()
    if exist:
        raise BusinessException(message="实验室名称已存在")

    lab = Lab(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def update_lab(lab_id: int, data: LabUpdateRequest, db: Session):
    """更新实验室"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室名称已存在")
    payload = data.model_dump(exclude_none=True)
    for filed, value in payload.items():
        setattr(lab, filed, value)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def delete_lab(lab_id: int, db: Session):
    """删除实验室"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")
    db.delete(lab)
    db.commit()
