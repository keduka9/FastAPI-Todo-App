from monsterui.all import *
from fasthtml.common import *
from sqlmodel import Session, select
from datetime import datetime, date
from fastapi import Depends
from .models.todo import Todo
from .core.database import get_session, created_db_and_tables

# app = FastHTML(hdrs=(Script(src="https://cdn.tailwindcss.com"),))
app =FastHTML()

# 起動時にテーブルを作成
@app.on_event("startup")
def startup():
    created_db_and_tables()
    print("🚀 TODOアプリ起動中...")

def todo_card(todo: Todo, today: date):
    """TODOカードを生成（ポートフォリオ向け 最終版）"""
    is_overdue = False
    is_today = False
    due_str = ""

    if todo.due_date:
        due_date_only = todo.due_date.date() if hasattr(todo.due_date, 'date') else todo.due_date
        is_overdue = due_date_only < today
        is_today = due_date_only == today
        due_str = f"📅 {todo.due_date.strftime('%Y-%m-%d')}"

    # 優先度ごとの色（インラインスタイルで確実に適用）
    priority_color = "#dc2626" if todo.priority == 1 else "#ea580c" if todo.priority == 2 else "#16a34a"

    # 優先度バッジ（すべての優先度でしっかり目立つ）
    # priority_cls = (
    #     "bg-red-600 text-white font-bold px-10 py-4 rounded-3xl text-lg shadow-xl" if todo.priority == 1 else
    #     "bg-orange-600 text-white font-bold px-10 py-4 rounded-3xl text-lg shadow-xl" if todo.priority == 2 else
    #     "bg-green-600 text-white font-bold px-10 py-4 rounded-3xl text-lg shadow-xl"
    # )

    due_cls = (
        "text-red-600 font-bold" if is_overdue else
        "text-orange-600 font-bold" if is_today else
        "text-gray-500"
    )

    return Card(
        Div(
            H3(todo.title, cls="font-semibold text-2xl tracking-tight mb-4"),
            P(todo.description or "", cls="text-gray-600 text-[15px] leading-relaxed mb-7"),
            Div(
                Span(f"優先度 {todo.priority}",
                    style=f"background-color: {priority_color}; color: white; font-weight: bold; padding: 1rem 2.5rem; border-radius: 1.5rem; fontsize: 1.125rem; box-shadow: 0.4px 6px -1px rgb(0 0 0 / 0.1);"
                ),
                Span(due_str, cls=f"ml-auto text-sm {due_cls}"),
                cls="flex items-center justify-between"
            ),
            cls="p-9"
        ),
        footer=Div(
            Button(
                "完了 ✓" if not todo.is_completed else "未完了に戻す",
                hx_patch=f"/todos/{todo.id}/complete",
                hx_target=f"#todo-{todo.id}",
                cls="px-10 py-4 text-base rounded-3xl font-medium transition-all shadow " +
                    ("bg-emerald-600 hover:bg-emerald-700 text-white" if not todo.is_completed else
                    "bg-gray-200 hover:bg-gray-300 text-gray-700")
            ),
            Button(
                "削除",
                hx_delete=f"/todos/{todo.id}",
                hx_target=f"#todo-{todo.id}",
                hx_confirm="本当に削除しますか？",
                cls="px-10 py-4 text-base bg-red-600 hover:bg-red-700 text-white rounded-3xl font-medium transition-all shadow"
            ),
            cls="flex gap-4 mt-9"
        ),
        id=f"todo-{todo.id}",
        cls="mb-8 bg-white border border-gray-100 shadow hover:shadow-2xl transition-all duration-300 rounded-3xl overflow-hidden"
    )

@app.get("/")
def index():
    session = next(get_session())
    try:
        todos = session.exec(select(Todo).order_by(Todo.priority.asc(), Todo.due_date.asc())).all()
        today = date.today()
    finally:
        session.close()

    return Title("FastAPI Todo App"), Main(
        H1("My TODOs", cls="text-4xl font-bold mb-8"),
        Form(
            Input(type="text", name="title", placeholder="TODOのタイトル", required=True),
            Input(type="text", name="description", placeholder="詳細（任意）"),
            Select(
                Option("高優先", value="1"),
                Option("中優先", value="2", selected=True),
                Option("低優先", value="3"),
                name="priority"
            ),
            Button("追加", type="submit"),
            hx_post="/todos/",
            hx_target="#todo-list",
            hx_swap="beforeend",
            cls="flex gap-3 mb-10"
        ),
        Div(id="todo-list", cls="space-y-4")(
            *[todo_card(todo, today) for todo in todos]
        ),
        cls="max-w-4xl mx-auto p-6 container"
    )

# CRUDエンドポイント（シンプルに残す）
@app.post("/todos/")
def create_todo(title: str, description: str = "", priority: int = 2):
    session = next(get_session())
    try:
        todo = Todo(title=title, description=description, priority=priority)
        session.add(todo)
        session.commit()
        session.refresh(todo)
        return todo_card(todo, date.today())    # HTMXで部分更新
    finally:
        session.close()

@app.patch("/todos/{todo_id}/complete")
def toggle_complete(todo_id: int):
    session = next(get_session())
    try:
        todo = session.get(Todo, todo_id)
        if todo:
            todo.is_completed = not todo.is_completed
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return todo_card(todo, date.today())
        return ""   # 空で返す
    finally:
        session.close()

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    session = next(get_session())
    try:
        todo = session.get(Todo, todo_id)
        if todo:
            session.delete(todo)
            session.commit()
            print(f"✅ TODO ID {todo_id} を削除しました")
            return "" 
        else:
            print(f"⚠️ TODO ID {todo_id} が見つかりません")
            return ""
    finally:
        session.close()

# サーバー起動
if __name__ == "__main__":
    serve()