from sqlmodel import SQLModel, create_engine, Session

# 使用绝对路径，确保与 Docker Compose 中挂载的 /data 目录一致
DATABASE_URL = "sqlite:////data/db.sqlite"
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Create database tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Return a Session bound to the global engine. Caller should use it as a context manager."""
    return Session(engine) 