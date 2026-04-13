from fastapi import FastAPI
from contextlib import asynccontextmanager

from .core.database import created_db_and_tables
from .routers.todo import router as todo_router     # <- items -> todoに変更
from .routers.frontend import router as frontend_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 TODOアプリ起動中... テーブルを作成します")
    created_db_and_tables()
    yield
    print("🛑 シャットダウン")

app = FastAPI(
    title="FastAPI TODO App",
    description="FastAPI + SQLModel + HTMXで作ったTODOアプリ",
    version="1.0.0",
    lifespan=lifespan
)

# ルーター登録
app.include_router(todo_router)
app.include_router(frontend_router)     # <- これを追加（重要！）

@app.get("/")
async def root():
    return {"message": "FastAPI TODOアプリが動いています！"}