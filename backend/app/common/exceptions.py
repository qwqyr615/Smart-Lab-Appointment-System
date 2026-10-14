from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.common.response import Response


class BusinessException(Exception):
    """自定义的业务异常"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


"""
request：请求对象（FastAPI 自动传入）
exc：被捕获的异常实例
"""


async def business_exception_handler(request: Request, exc: BusinessException):
    """自定义业务异常处理器"""
    return JSONResponse(
        status_code=200,
        content=Response(code=exc.code, message=exc.message).model_dump(),
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=Response.error(code=exc.status_code, message=exc.detail).model_dump(),
    )


async def validation_exeception_handler(request: Request, exc: RequestValidationError):
    """参数异常处理器"""
    return JSONResponse(
        status_code=422,
        content=Response.error(code=422, message="请求参数校验错误").model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    return JSONResponse(
        status_code=500,
        content=Response.error(code=500, message="服务器内部错误").model_dump(),
    )
