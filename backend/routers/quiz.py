import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.llm import generate_quiz
from backend.models import Quiz, QuizQuestion, QuizSubmission, Topic

router = APIRouter(prefix="/api/quiz", tags=["quiz"])
logger = logging.getLogger(__name__)


# ── Request / response models ──────────────────────────────────────────────

class QuizOptionResponse(BaseModel):
    id: int
    order: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    # correct + explanation intentionally omitted — revealed only after submission

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    quiz_id: int
    topic_id: int
    questions: list[QuizOptionResponse]


class SubmitRequest(BaseModel):
    device_id: str
    answers: dict[str, str]  # {"1": "a", "2": "b", ...} keyed by question order


class QuestionResult(BaseModel):
    order: int
    question: str
    your_answer: str
    correct: str
    correct_text: str   # the text of the correct option
    is_correct: bool
    explanation: str


class SubmitResponse(BaseModel):
    score: int
    total: int
    results: list[QuestionResult]


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_completed: int
    activity: list[str]  # list of YYYY-MM-DD dates where quiz was submitted


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/streak", response_model=StreakResponse)
def get_streak(device_id: str, db: Session = Depends(get_db)):
    """Return streak stats and activity dates for a device."""
    if not device_id or len(device_id) > 64:
        raise HTTPException(status_code=400, detail="Invalid device_id")

    submissions = (
        db.query(QuizSubmission)
        .join(Topic, QuizSubmission.topic_id == Topic.id)
        .filter(QuizSubmission.device_id == device_id)
        .with_entities(Topic.date)
        .all()
    )

    completed_dates = sorted({row.date for row in submissions})

    # Current streak: consecutive days ending today or yesterday
    current_streak = 0
    today = date.today()
    check = today
    date_set = set(completed_dates)
    while check.isoformat() in date_set:
        current_streak += 1
        check = check - timedelta(days=1)
    # If today not done, check if yesterday starts a streak
    if current_streak == 0:
        check = today - timedelta(days=1)
        while check.isoformat() in date_set:
            current_streak += 1
            check = check - timedelta(days=1)

    # Longest streak
    longest_streak = 0
    if completed_dates:
        run = 1
        for i in range(1, len(completed_dates)):
            prev = date.fromisoformat(completed_dates[i - 1])
            curr = date.fromisoformat(completed_dates[i])
            if (curr - prev).days == 1:
                run += 1
                longest_streak = max(longest_streak, run)
            else:
                run = 1
        longest_streak = max(longest_streak, run)

    return StreakResponse(
        current_streak=current_streak,
        longest_streak=longest_streak,
        total_completed=len(completed_dates),
        activity=completed_dates,
    )


@router.post("/{topic_id}/generate", response_model=QuizResponse)
def generate_quiz_public(topic_id: int, db: Session = Depends(get_db)):
    """Generate a quiz for a topic if one doesn't already exist (public, idempotent)."""
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    existing = db.query(Quiz).filter(Quiz.topic_id == topic_id).first()
    if existing:
        # Already exists — just return it
        questions = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.quiz_id == existing.id)
            .order_by(QuizQuestion.order)
            .all()
        )
        return QuizResponse(quiz_id=existing.id, topic_id=topic_id, questions=questions)

    try:
        quiz_questions = generate_quiz(topic.title, topic.problem_statement, topic.deep_dive)
    except Exception as e:
        logger.error(f"Quiz generation failed for topic {topic_id}: {e}")
        raise HTTPException(status_code=502, detail="Quiz generation failed — try again shortly")

    quiz = Quiz(topic_id=topic_id)
    db.add(quiz)
    db.flush()
    for i, q in enumerate(quiz_questions, start=1):
        db.add(QuizQuestion(
            quiz_id=quiz.id,
            order=i,
            question=q["question"],
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct=q["correct"],
            explanation=q["explanation"],
        ))
    db.commit()
    db.refresh(quiz)

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz.id)
        .order_by(QuizQuestion.order)
        .all()
    )
    return QuizResponse(quiz_id=quiz.id, topic_id=topic_id, questions=questions)


@router.get("/{topic_id}", response_model=QuizResponse)
def get_quiz(topic_id: int, db: Session = Depends(get_db)):
    """Get quiz questions for a topic (correct answers NOT included)."""
    quiz = db.query(Quiz).filter(Quiz.topic_id == topic_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found for this topic")

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz.id)
        .order_by(QuizQuestion.order)
        .all()
    )

    return QuizResponse(
        quiz_id=quiz.id,
        topic_id=topic_id,
        questions=questions,
    )


@router.post("/{quiz_id}/submit", response_model=SubmitResponse)
def submit_quiz(quiz_id: int, body: SubmitRequest, db: Session = Depends(get_db)):
    """Submit answers for a quiz. One attempt per device per quiz."""
    if not body.device_id or len(body.device_id) > 64:
        raise HTTPException(status_code=400, detail="Invalid device_id")

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # One attempt per device
    existing = (
        db.query(QuizSubmission)
        .filter(QuizSubmission.quiz_id == quiz_id, QuizSubmission.device_id == body.device_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already submitted")

    questions = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == quiz_id)
        .order_by(QuizQuestion.order)
        .all()
    )

    option_text_map = {"a": "option_a", "b": "option_b", "c": "option_c", "d": "option_d"}

    results = []
    score = 0
    for q in questions:
        key = str(q.order)
        your_answer = body.answers.get(key, "").lower()
        is_correct = your_answer == q.correct
        if is_correct:
            score += 1

        correct_text = getattr(q, option_text_map.get(q.correct, "option_a"), "")
        results.append(QuestionResult(
            order=q.order,
            question=q.question,
            your_answer=your_answer,
            correct=q.correct,
            correct_text=correct_text,
            is_correct=is_correct,
            explanation=q.explanation,
        ))

    submission = QuizSubmission(
        device_id=body.device_id,
        quiz_id=quiz_id,
        topic_id=quiz.topic_id,
        score=score,
        answers=body.answers,
    )
    db.add(submission)
    db.commit()

    return SubmitResponse(score=score, total=len(questions), results=results)
