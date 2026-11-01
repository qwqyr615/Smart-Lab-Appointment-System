from fastapi import APIRouter, Depends
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ai import ChatRequest
from app.service import agent_service
import json
from fastapi.responses import StreamingResponse
from app.database import SessionLocal
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI相关的API"])


def _to_sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat(data: ChatRequest, current_user: User = Depends(get_current_user)):
    user_id = current_user.id

    async def event_stream():
        db = SessionLocal()
        try:
            user = db.get(User, user_id)
            async for event in agent_service.stream_agent(db, user, data):
                yield _to_sse(event)
        finally:
            db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx 不缓冲
            "Connection": "keep-alive",
        },
    )
