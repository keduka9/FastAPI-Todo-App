from fasthtml.common import *
from monsterui.all import *
from fastapi import Request, Depends
from sqlmodel import Session, select
from ..models.todo import Todo
from ..dependencies import get_session
from datetime import date

# FastHTMLアプリ（FastAPIと共存させるためにAPIRouter風に使う）
fasthtml_app = FastHTML()

@fasthtml_app.get("/")
def incex(request: Request, session: Session = Depends(get_session)):
    todos = session.exec(select(Todo).order_by(Todo.priority.asc(), Todo.due_date.asc())).all()
    today = date.today()

    def todo_card(todo: Todo):
        is_overdue = todo.due_date and todo.due_date.date() < today
        is_today = todo.due_date and todo.due_date.date() == today

        # 優先度バッジ（Tailwindで直接指定 - 最も安定）
        priority_cls = ("bg-red-100 text-red-700 font-medium" if todo.priority == 1 else
                        "bg-orange-100 text-orange-700 font-medium" if todo.priority == 2 else
                        "bg-green-100 text-green-700 font-medium")

        due_cls = (
            "text-red-600 font-bold" if is_overdue else
            "text-orange-600 font-bold" if is_today else
            "text-gray-500"
        )

        return Card(
            Div(
                H3(todo.title, cls="font-semibold text-lg"),
                P(todo.description or "", cls="text-sm text-gray-600 mt-1"),
                Div(
                    Span(f"優先度 {todo.priority}", cls=f"inline-block px-4 py-1.5 rounded-full text-sm {priority_cls}"),
                    Span(f"📅 {todo.due_date.strftime('%Y-%m-%d')}" if todo.due_date else "",
                        cls=f"ml-6 text-sm {due_cls}"),
                    cls="flex items-center mt-4"
                ),
                cls="p-6"
            ),
            footer=Div(
                Button(
                    "完了 ✓" if not todo.is_completed else "未完了に戻す",
                    hx_patch=f"/todos/{todo.id}/complete",
                    hx_target=f"#todo-{todo.id}",
                    cls="px-6 py-2.5 text-sm rounded-2xl font-medium transition " + 
                        ("bg-emerald-500 hover:bg-emerald-600 text-white shadow-sm" if not todo.is_completed else "bg-gray-200 hover:bg-gray-300 text-gray-700")
                ),
                Button(
                    "削除",
                    hx_delete=f"/todos/{todo.id}",
                    hx_target=f"#todo-{todo.id}",
                    hx_confirm="本当に削除しますか？",
                    cls="px-6 py-2.5 text-sm bg-red-500 hover:bg-red-600 text-white rounded-2xl font-medium transition"
                ),
                cls="flex gap-4 mt-6"
            ),
            id="todo-{todo.id}",
            cls="mb-6 shadow-sm border border-gray-100"
        )
    
    return Title("FastAPI Todo App"), Container(
            H1("My TODOs", cls="text-4xl font-bold mb-8"),
            Form(
                Input(type="text", name="title", Placeholder="TODOのタイトル", required=True),
                Input(type="text", name="description", Placeholder="詳細（任意）"),
                Select(
                    Option("高優先", value=1),
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
                *[todo_card(todo) for todo in todos]
            ),
            cls="max-w-4xl mx-auto p-6"
        )
    
# FastAPIにマウント（重要）
def mount_fasthtml(app):
    app.mount("/", fasthtml_app)
    