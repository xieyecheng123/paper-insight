import os
from contextlib import contextmanager
from sqlmodel import create_engine, Session, SQLModel
from urllib.parse import quote_plus

# 从独立的环境变量构造数据库连接 URL
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "paper_insight")

# URL-encode 密码以处理特殊字符
encoded_password = quote_plus(DB_PASSWORD)

DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 创建数据库引擎
# connect_args 是特定于 SQLite 的，对于 PostgreSQL 我们不需要它
# echo=True 会打印出所有执行的 SQL 语句，便于调试
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    # 创建所有在 SQLModel 中定义的表
    SQLModel.metadata.create_all(engine)


# 这是为 FastAPI 依赖注入系统设计的生成器
def get_session():
    with Session(engine) as session:
        yield session


# 这是为 Celery 任务或其他后台脚本设计的上下文管理器
@contextmanager
def get_session_for_task():
    """Provide a transactional scope around a series of operations."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close() 