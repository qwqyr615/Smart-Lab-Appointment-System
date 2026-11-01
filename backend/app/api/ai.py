import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.database import SessionLocal
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.service import agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI相关的API"])

# 队列里的结束哨兵
_STREAM_END = object()


def _to_sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _log_background_error(task: asyncio.Task) -> None:
    """后台任务的异常要在回调里取走，否则会变成 "Task exception was never retrieved"。"""
    if task.cancelled():
        return
    if (exc := task.exception()) is not None:
        logger.error("流式对话后台任务异常", exc_info=exc)


@router.post("/chat/stream")
async def chat(data: ChatRequest, current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()

        async def produce():
            db = SessionLocal()
            try:
                user = db.get(User, user_id)
                if user is None:
                    await queue.put(
                        {"type": "error", "message": "登录已失效，请重新登录"}
                    )
                    return
                async for event in agent_service.stream_agent(db, user, data):
                    await queue.put(event)
            except Exception:
                logger.exception("流式对话执行失败")
                await queue.put(
                    {"type": "error", "message": "服务器内部错误，请稍后重试"}
                )
            finally:
                db.close()
                await queue.put(_STREAM_END)

        # 单独的 session 归 produce 所有：客户端断开时生成器会被取消，
        # 但同步工具跑在线程池里取消不掉，session 必须等它跑完才能关。
        task = asyncio.create_task(produce())

        try:
            while True:
                event = await queue.get()
                if event is _STREAM_END:
                    break
                yield _to_sse(event)
        finally:
            # 用户关页面/点停止：不再读队列，produce 继续收尾并自行关闭 session
            task.add_done_callback(_log_background_error)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx 不缓冲
        },
    )
