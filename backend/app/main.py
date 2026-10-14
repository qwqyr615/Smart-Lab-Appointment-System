from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from app.models.user import User
from app.database import Base, engine
from app.api import api
from app.common.exceptions import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exeception_handler,
    global_exception_handler,
)

Base.metadata.create_all(bind=engine)  # 自动帮我们创建数据库表

app = FastAPI()
app.include_router(api)

# 注册异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exeception_handler)
# 全局的异常兜底，放在最后注册
app.add_exception_handler(Exception, global_exception_handler)


@app.get("/")
def root():
    return {"message": "FastAPI工程正在运行中"}
