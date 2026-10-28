import json
import traceback
from pydantic import Json
from sqlalchemy.orm import Session
from openai import OpenAI
from app.common.exceptions import BusinessException
from app.config import settings
from app.schemas.ai import ChatMessage, ChatRequest
from app.service import kb_service, lab_service, equipment_service
from app.service.kb_service import search

SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
如果下面提供了实验室资料，请依据资料回答规则、安全、文档里的开放时间说明。
查询当前有哪些开放实验室、某实验室有哪些设备时，必须调用工具，不要编造。
用户明确给出实验室 ID 时，直接查询该实验室的设备，无需再次确认 ID。
你不能替用户提交预约，也不能直接改数据库。
如果用户要预约，请说明去「实验室列表」选择后提交，等待管理员审核。
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_open_labs",
            "description": "查询当前开放中的实验室列表，可以按名称关键字来筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "实验室的名称关键字，可以为空",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_lab_equipments",
            "description": "查询某个实验室下的设备列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab_id": {
                        "type": "integer",
                        "description": "实验室 ID",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "设备名称的关键字，可以为空",
                    },
                },
                "required": ["lab_id"],
            },
        },
    },
]


def get_client() -> OpenAI:
    """创建OPENAI的客户端"""
    if not settings.LLM_API_KEY:
        raise BusinessException(message="未获取到大模型的API KEY")
    return OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)


def chat(data: ChatRequest, db: Session):
    """大模型对话"""
    if not data.messages:
        raise BusinessException(message="对话内容为空")
    history = []
    for message in data.messages:
        if message.role in ("user", "assistant") and message.content.strip():
            history.append(message.model_dump())
    if not history:
        raise BusinessException(message="请输入您要对话的内容")

    # 取出用户最新的一条提问内容
    question = next(
        (item["content"] for item in reversed(history) if item["role"] == "user"), ""
    )

    knowledge = kb_service.search(query=question)

    print(f"检索到的向量库的内容: {knowledge}")
    system_prompt = SYSTEM_PROMPT
    if knowledge:
        system_prompt += "\n\n以下是检索到的实验室的资料:\n" + knowledge

    client = get_client()

    messages = [
        {"role": "system", "content": system_prompt},
        *history,  # 展开运算符，把历史消息全部加入
    ]

    print("\n[chat] 提供给模型的工具定义 TOOLS:", flush=True)
    print(json.dumps(TOOLS, ensure_ascii=False, indent=2), flush=True)

    try:
        for round_no in range(1, 4):
            print(f"\n[chat 第 {round_no} 轮] 发送给模型的 messages:", flush=True)
            print(json.dumps(messages, ensure_ascii=False, indent=2), flush=True)
            res = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            msg = res.choices[0].message
            print(f"\n[chat 第 {round_no} 轮] 模型返回的 msg:", flush=True)
            print(json.dumps(msg.model_dump(exclude_none=True), ensure_ascii=False, indent=2), flush=True)
            print(f"[chat 第 {round_no} 轮] finish_reason: {res.choices[0].finish_reason}", flush=True)
            tool_calls = msg.tool_calls or []
            if not tool_calls:  # 没有工具调用 则直接返回大模型的输出结果内容
                content = msg.content
                if not content or not content.strip():
                    raise BusinessException(message="大模型没有返回内容")
                return content
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments,
                            },
                        }
                        for call in tool_calls
                    ],
                }
            )

            for call in tool_calls:
                print(f"\n[chat 第 {round_no} 轮] 执行工具 {call.function.name}:", flush=True)
                print(f"  tool_call_id: {call.id}", flush=True)
                print(f"  arguments (JSON 字符串): {call.function.arguments}", flush=True)
                result = run_tool(db, call.function.name, call.function.arguments)
                print(f"  result (JSON 字符串): {result}", flush=True)
                messages.append(
                    {"role": "tool", "content": result, "tool_call_id": call.id}
                )
    except Exception as exc:
        traceback.print_exc()
        raise BusinessException(message="大模型调用失败，请稍后重试")


def run_tool(db: Session, name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        return json.dumps({"error": "参数不是合法的json"}, ensure_ascii=False)

    try:
        if name == "list_open_labs":
            keywords = (args.get("keywords") or "").strip() or None
            page = lab_service.get_lab_page_list(
                db=db, page=1, page_size=10, keywords=keywords, status=1
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
            return json.dumps({"total": page.total, "labs": rows}, ensure_ascii=False)

        if name == "list_lab_equipments":
            lab_id = args.get("lab_id")
            if lab_id is None:
                return json.dumps(
                    {"error": "参数缺少实验室 lab_id"}, ensure_ascii=False
                )
            keywords = args.get("keywords")
            page = equipment_service.get_equipment_page_list(
                db=db, page=1, page_size=10, lab_id=int(lab_id), keywords=keywords
            )
            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "lab_id": item.lab_id,
                    "lab_name": item.lab_name,
                    "spec": item.spec,
                    "quantity": item.quantity,
                    "status": item.status,
                }
                for item in page.list
            ]
            return json.dumps(
                {"total": page.total, "equipments": rows}, ensure_ascii=False
            )
        return json.dumps({"error": f"未找到工具：{name}"}, ensure_ascii=False)

    except Exception as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
