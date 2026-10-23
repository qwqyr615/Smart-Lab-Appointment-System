from fastapi import APIRouter, Depends
from app.common.response import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.lab import LabUpdateRequest, LabCreateRequest
from app.service import lab_service
from app.dependencies.auth import get_current_admin, get_current_user

router = APIRouter(prefix="/lab", tags=["实验室管理"])


@router.get("/list")
def get_lab_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    status: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visible_status = status if current_user.role == "admin" else 1
    res = lab_service.get_lab_page_list(
        page=page, page_size=page_size, status=visible_status, db=db, keywords=keywords
    )
    return Response.success(data=res)


@router.get("/{lab_id}")
def get_lab(
    lab_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    visible_status = None if current_user.role == "admin" else 1
    res = lab_service.get_lab(lab_id, db, status=visible_status)
    return Response.success(data=res)


@router.post("")
def create_lab(
    data: LabCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = lab_service.create_lab(data, db)
    return Response.success(data=res)


@router.put("/{lab_id}")
def update_lab(
    lab_id: int,
    data: LabUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = lab_service.update_lab(lab_id, data, db)
    return Response.success(data=res)


@router.delete("/{lab_id}")
def delete_lab(
    lab_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    lab_service.delete_lab(lab_id, db)
    return Response.success("实验室删除成功")
