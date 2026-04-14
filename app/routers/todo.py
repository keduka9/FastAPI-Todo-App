from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response, Body
from sqlmodel import Session, select
from ..schemas.todo import TodoCreate, TodoResponse
from ..models.todo import Todo
from ..dependencies import get_session
from typing import Optional # 追加
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import date, datetime

router = APIRouter(prefix="/todos", tags=["todos"])
templates = Jinja2Templates(directory="app/templates")

@router.post("/")
async def create_todo(
    request: Request,
    todo_in: TodoCreate,
    session: Session = Depends(get_session)

):
    # dict()を使って辞書として展開し、Todoモデルを作成
    new_todo = Todo(
        title=todo_in.title,
        description=todo_in.description,
        priority=todo_in.priority,
        due_date=todo_in.due_date,      # ここで確実にdue_dateを渡す
        is_completed=False
    )

    session.add(new_todo)
    session.commit()
    session.refresh(new_todo)

    # JSONではなく、1件分のTODOを表示するHTMLテンプレートを返す
    return templates.TemplateResponse(
        request=request,
        name="todo_item.html",
        context={"todo": new_todo, "today": date.today()}
    )

# @router.get("/", response_model=list[TodoResponse])   TODO全体を表示させるように変更する
@router.get("/", response_class=HTMLResponse)
# async def read_todos(session: Session = Depends(get_session)):    ここにも変更を加える
async def read_todos(request: Request, session: Session = Depends(get_session)):
    """TODO一覧をHTMLで返す（HTMX用）"""
    statement = select(Todo).order_by(Todo.priority.asc(), Todo.due_date.asc())
    todos = session.exec(statement).all()

    # テンプレートを返す（Jinja2のループ機能を使って全件表示する）
    # こちらが最新の書き方で、エラーを回避できる
    return templates.TemplateResponse(
        request=request,
        name="todo_list_inner.html",    # 新しく作るファイル
        context={
            "today": date.today(),
            "todos": todos
        }
    )

    # こっちは古い書き方で、エラーが出てしまうので、コメントアウト
    # return templates.TemplateResponse("todo_list_inner.html", {
    #     "request": request,
    #     "todos": todos
    # })

@router.get("/{todo_id}", response_model=TodoResponse)
async def read_todo(todo_id: int, session: Session = Depends(get_session)):
    statement = select(Todo).where(Todo.id == todo_id)
    todo = session.exec(statement).first()
    if todo is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    return todo

@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(todo_id: int, todo_update: TodoCreate, session: Session = Depends(get_session)):
    statement = select(Todo).where(Todo.id == todo_id)
    db_todo = session.exec(statement).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    
    db_todo.title = todo_update.title
    db_todo.description = todo_update.description
    db_todo.priority = todo_update.priority
    db_todo.due_date = todo_update.due_date

    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo

# @router.patch("/{todo_id}/complete", response_model=TodoResponse)
@router.patch("/{todo_id}/complete")
async def toggle_complete(
    request: Request,   # 追加
    todo_id: int,
    session: Session = Depends(get_session)
):
    """完了状態をトグル（完了↔未完了）"""
    statement = select(Todo).where(Todo.id == todo_id)
    db_todo = session.exec(statement).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    
    # 状態を反転させて保存
    db_todo.is_completed = not db_todo.is_completed
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)

    # 修正ポイント：JSONではなく、更新後のHTMLを返す
    return templates.TemplateResponse(
        request=request,
        name="todo_item.html",
        context={"todo": db_todo, "today": date.today()}
    )
@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    statement = select(Todo).where(Todo.id == todo_id)
    db_todo = session.exec(statement).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    
    session.delete(db_todo)
    session.commit()

    # 修正ポイント：メッセージを返さず、空のレスポンスを返す
    # これにより HTMX がターゲット（todo_item）を「空」で上書きして消してくれます
    return Response(status_code=200)

    # メッセージをJSONで返してしまい、削除後の画面上にJSONのメッセージが表示されてしまうので、コメントアウト
    # return {"message": f"Todo with id {todo_id} has been deleted successfully"}