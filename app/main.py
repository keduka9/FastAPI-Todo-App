from monsterui.all import *
from fasthtml.common import *
from sqlmodel import Session, select
from datetime import datetime, date
from fastapi import Depends
from .models.todo import Todo
from .core.database import get_session, created_db_and_tables

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
    if todo.priority == 1:
        priority_style = "background-color: #dc2626; color: white; font-weight: bold; padding: 16px 40px; border-radius: 9999px; font-size: 1.125rem; box-shadow: 0 10px 15px -3px rgb(220 38 38 / 0.3);"
    elif todo.priority == 2:
        priority_style = "background-color: #ea580c; color: white; font-weight: bold; padding: 16PX 40PX; border-radius: 9999px; font-size: 1.125rem; box-shadow: 0 10px 15px -3px rgb(234 88 12 / 0.3);"
    else:
        priority_style = "background-color: #16a34a; color: white; font-weight: bold; padding: 16PX 40PX; border-radius: 9999px; font-size: 1.125rem; box-shadow: 0 10px 15px -3px rgb(22 163 74 / 0.3);"

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
                Span(f"優先度 {todo.priority}", style=priority_style),
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

        todo_list = (
            [todo_card(todo, today) for todo in todos] if todos else 
            [Div(
                P("まだTODOがありません。", cls="text-gray-500 text-center py-16 text-lg"),
                P("新しいタスクを追加して始めましょう！", cls="text-gray-400 text-center mt-2"),
                cls="col-span-full py-12"
            )]
        )

        return Title("FastAPI Todo App"), Main(
            H1("My TODOs", cls="text-4xl font-bold mb-8"),
            Form(
                Div(
                    Input(type="text", name="title", placeholder="TODOのタイトル", required=True),
                    cls="flex-1 min-w-[200px]"
                ),
                Div(
                    Input(type="text", name="description", placeholder="詳細（任意）"),
                    cls="flex-1 min-w-[200px]"
                ),
                Div(
                    Input(
                        type="date",
                        name="due_date",
                        cls="px-4 py-2.5 border border-gray-300 rounded-2xl focus:outline-none focus-:ring-2 focus:ring-blue-500"
                    ),
                    cls="min-w-[160px]"
                ),
                #   期限日入力フォームを追加
                Div(
                    Select(
                        Option("高優先", value="1"),
                        Option("中優先", value="2", selected=True),
                        Option("低優先", value="3"),
                        name="priority"
                    ),
                    cls="min-w-[120px]"
                ),
                Button("追加", type="submit"),
                hx_post="/todos/",
                hx_target="#todo-list",
                hx_swap="beforeend",
                cls="flex gap-3 mb-10 flex-wrap items-end"
            ),
            Div(id="todo-list", cls="space-y-4")(*todo_list),
            cls="max-w-4xl mx-auto p-6"
        )
    finally:
        session.close()

    

# CRUDエンドポイント（シンプルに残す）
@app.post("/todos/")
def create_todo(title: str, description: str = "", priority: int = 2, due_date: str | None = None):
    """TODOを作成"""
    session = next(get_session())
    try:
        due_date_obj = None
        if due_date:
            try:
                due_date_obj = date.fromisoformat(due_date)
            except ValueError:
                due_date_obj = None     # 日付形式が不正な場合は無視

        todo = Todo(
            title=title,
            description=description, 
            priority=priority,
            due_date=due_date_obj
        )
        session.add(todo)
        session.commit()
        session.refresh(todo)

        print(f"✅ 新しいTODOを作成しました: {title}（期限: {due_date_obj}）")
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