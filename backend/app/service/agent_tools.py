from datetime import datetime
import json

from sqlalchemy.orm import Session
from app.common.exceptions import BusinessException
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest
from langchain_core.tools import tool
from pydantic import ValidationError

from app.service import equipment_service, kb_service, lab_service, reservation_service


# 组装并交出可用的工具集合
def build_tools(db: Session, current_user: User):

    @tool
    def search_lab_docs(query: str) -> str:
        """根据用户的提问检索知识库"""
        try:
            return kb_service.search(query) or "没有检索到相关资料"
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_open_labs(keywords: str = "") -> str:
        """查询开放的实验室列表。参数 keywords 应为实验室名称的关键词，如"生物"、"物理"等，不要传入整句用户问题。"""
        try:
            keywords = keywords.strip() or None
            page = lab_service.get_lab_page_list(
                page=1, page_size=20, db=db, keywords=keywords, status=1
            )
            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "location": item.location,
                    "capacity": item.capacity,
                    "open_time": item.open_time,
                    "close_time": item.close_time,
                }
                for item in page.list
            ]
            return json.dumps({"labs": rows, "total": page.total}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_lab_equipments(lab_id: int, keywords: str = "") -> str:
        """查询某个实验室的设备列表"""
        try:
            keywords = keywords.strip() or None
            page = equipment_service.get_equipment_page_list(
                db, page=1, page_size=10, lab_id=int(lab_id), keywords=keywords
            )
            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "lab_id": item.lab_id,
                    "lab_name": item.lab_name,
                    "sepc": item.spec,
                    "quantity": item.quantity,
                    "status": item.status,
                }
                for item in page.list
            ]
            return json.dumps(
                {"total": page.total, "equipments": rows}, ensure_ascii=False
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def create_lab_reservation(
        lab_id: int,
        date: str,
        start_time: str,
        end_time: str,
        equipment_id: int | None = None,
        remark: str | None = None,
    ) -> str:
        """创建预约单预约实验室或设备"""
        try:
            data = ReservationCreateRequest(
                lab_id=lab_id,
                equipment_id=equipment_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                remark=remark,
            )
            reservation_service.create_reservation(
                db=db, current_user=current_user, data=data
            )
            return json.dumps(
                {
                    "ok": True,
                    "message": "预约已提交，请等待管理员审核",
                    "lab_id": lab_id,
                    "equipment_id": equipment_id,
                    "date": date,
                    "start_time": start_time,
                    "end_time": end_time,
                },
                ensure_ascii=False,
            )
        # BusinessException：项目主动抛出的业务错误，例如“预约时间冲突”。它的提示文字放在 exc.message 中
        # Exception：兜底处理其他错误，例如数据库异常、代码运行错误。这里用 str(exc) 取得异常文字
        except BusinessException as exc:
            return json.dumps({"ok": False, "error": exc.message}, ensure_ascii=False)
        except ValidationError as exc:
            error = exc.errors()[0]
            return json.dumps(
                {"ok": False, "error": f"预约参数格式错误：{'.'.join(map(str, error['loc']))} {error['msg']}"},
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def get_today() -> str:
        """获取服务器当前的日期"""
        now = datetime.now()
        return now.strftime("%Y-%m-%d")

    return [
        search_lab_docs,
        list_open_labs,
        list_lab_equipments,
        create_lab_reservation,
        get_today,
    ]
