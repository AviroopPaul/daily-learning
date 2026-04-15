from sqlalchemy import create_engine, text
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


DEFAULT_SUBJECT_AREAS = [
    "Databases",
    "Distributed Systems",
    "Caching",
    "System Design Fundamentals",
    "Networking",
    "Security",
    "API Design",
    "Message Queues",
    "Observability & Monitoring",
    "Load Balancing",
    "Storage Systems",
    "Consensus & Coordination",
    "Rate Limiting",
    "Authentication & Authorization",
    "Search Systems",
    "Stream Processing",
    "Data Pipelines",
    "Container Orchestration",
    "Service Discovery",
    "Edge Computing & CDN",
    "LLM Infrastructure",
    "CI/CD & DevOps",
]


def init_db():
    from backend.models import Topic, PushSubscription, SubjectArea  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Add new columns that didn't exist in older schema versions
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE topics ADD COLUMN tldr TEXT"))
            conn.commit()
        except Exception:
            pass  # column already exists

    # Seed default subject areas on first run
    db = SessionLocal()
    try:
        if db.query(SubjectArea).count() == 0:
            for name in DEFAULT_SUBJECT_AREAS:
                db.add(SubjectArea(name=name))
            db.commit()
    finally:
        db.close()
