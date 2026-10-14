from fastapi import FastAPI
from app.models.user import User
from app.database import Base, engine
from app.api import api

Base.metadata.create_all(bind=engine)  # 自动帮我们创建数据库表

app = FastAPI()
app.include_router(api)


@app.get("/")
def root():
    return {"message": "FastAPI工程正在运行中"}
