from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.database import get_db
from backend.models import Topic
from backend.schemas import TopicResponse, TopicListItem

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("", response_model=list[TopicListItem])
def list_topics(db: Session = Depends(get_db)):
    topics = (
        db.query(Topic)
        .order_by(desc(Topic.date))
        .all()
    )
    return topics


@router.get("/today", response_model=TopicResponse)
def get_today_topic(db: Session = Depends(get_db)):
    from datetime import date
    today = date.today().isoformat()
    topic = db.query(Topic).filter(Topic.date == today).first()
    if not topic:
        raise HTTPException(status_code=404, detail="No topic generated yet for today")
    return topic


@router.get("/{topic_id}", response_model=TopicResponse)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
