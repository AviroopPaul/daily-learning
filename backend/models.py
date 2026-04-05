from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from backend.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), unique=True, index=True, nullable=False)  # YYYY-MM-DD
    title = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False, default="Intermediate")
    problem_statement = Column(Text, nullable=False)
    context_text = Column(Text, nullable=False)
    deep_dive = Column(Text, nullable=False)
    real_world_examples = Column(Text, nullable=False)
    solution_approaches = Column(Text, nullable=False)
    key_takeaways = Column(JSON, nullable=False, default=list)
    further_reading = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SubjectArea(Base):
    __tablename__ = "subject_areas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(Text, unique=True, nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
