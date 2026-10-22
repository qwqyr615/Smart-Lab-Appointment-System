from fastapi import APIRouter, Depends
from app.common.response import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.equipment import EquipmentUpdateRequest, EquipmentCreateRequest
from app.service import equipment_service
from app.dependencies.auth import get_current_admin

router = APIRouter(prefix="/equipment", tags=["实验室设备信息接口"])


@router.get("/list")
def get_equipment_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    lab_id: int | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = equipment_service.get_equipment_page_list(
        page=page, page_size=page_size, db=db, keywords=keywords, lab_id=lab_id
    )
    return Response.success(data=res)


@router.post("")
def create_equipment(
    data: EquipmentCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = equipment_service.create_equipment(data, db)
    return Response.success(data=res)


@router.put("/{equipment_id}")
def update_equipment(
    equipment_id: int,
    data: EquipmentUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = equipment_service.update_equipment(equipment_id, data, db)
    return Response.success(data=res)


@router.delete("/{equipment_id}")
def delete_equipment(
    equipment_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    equipment_service.delete_equipment(equipment_id, db)
    return Response.success("实验室设备删除成功")
