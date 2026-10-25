import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.database import Base, engine
from app.api import api
from app.common.exceptions import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exeception_handler,
    global_exception_handler,
)
from starlette.middleware.cors import CORSMiddleware

from app.service import reservation_service

Base.metadata.create_all(bind=engine)  # 自动帮我们创建数据库表


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动项目开始一步的扫描任务
    task = asyncio.create_task(reservation_service.run_expire_scan())
    yield
    # 关闭项目同时取消异步任务
    task.cancel()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源
    allow_credentials=True,  # 允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
)

app.include_router(api)

# 注册异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exeception_handler)
# 全局的异常兜底，放在最后注册
app.add_exception_handler(Exception, global_exception_handler)

# 挂在静态的文件目录  http://127.0.0.1:8000/uploads/xxx.jpg
app.mount("/upload", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def root():
    return {"message": "FastAPI工程正在运行中"}
