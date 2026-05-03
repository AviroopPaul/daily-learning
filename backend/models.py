from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from backend.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), unique=True, index=True, nullable=False)  # YYYY-MM-DD
    title = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False, default="Intermediate")
    tldr = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=False)
    context_text = Column(Text, nullable=False)
    deep_dive = Column(Text, nullable=False)
    real_world_examples = Column(Text, nullable=False)
    solution_approaches = Column(Text, nullable=False)
    mermaid_diagram = Column(Text, nullable=True)
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


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    order = Column(Integer, nullable=False)        # 1–5
    question = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct = Column(String(1), nullable=False)    # "a"|"b"|"c"|"d"
    explanation = Column(Text, nullable=False)


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), index=True, nullable=False)  # UUID from browser localStorage
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    score = Column(Integer, nullable=False)        # 0–5
    answers = Column(JSON, nullable=False)         # {"1": "a", "2": "c", ...}
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
