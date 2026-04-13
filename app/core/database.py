from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

# SQLiteデータベースファイル（プロジェクトフォルダにdb.sqlitができる）
DATABASE_URL = "sqlite:///db.sqlite"

# エンジン作成（echo=True でSQLログが見えるようになる。開発時は便利）
engine = create_engine(DATABASE_URL, echo=True)

# テーブルを作成する関数（アプリ起動時に呼ぶ）
def created_db_and_tables():
    SQLModel.metadata.create_all(engine)

# FastAPI Dependency :DBセッションを提供
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session