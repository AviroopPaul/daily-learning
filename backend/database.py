from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/topics.db")

# For SQLite, use check_same_thread=False and StaticPool for thread safety
connect_args = {}
poolclass = None

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if DATABASE_URL == "sqlite:///:memory:":
        poolclass = StaticPool

engine_kwargs = {"connect_args": connect_args}
if poolclass:
    engine_kwargs["poolclass"] = poolclass

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend.models import Topic, PushSubscription  # noqa: F401
    Base.metadata.create_all(bind=engine)
