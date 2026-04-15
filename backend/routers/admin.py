import logging
from datetime import date
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Topic, PushSubscription, SubjectArea
from backend.schemas import GenerateResponse, TopicListItem
from backend.llm import generate_topic, generate_tldr, get_llm_config, update_llm_config, compute_target_difficulty, DIFFICULTY_LEVELS
from backend.email_service import send_topic_email
from backend.push_service import send_push_notification
import os

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)


# ── Request / response models ──────────────────────────────────────────────

class TriggerRequest(BaseModel):
    model: Optional[str] = None


class ConfigRequest(BaseModel):
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    topic_prompt_template: Optional[str] = None
    difficulty_mode: Optional[str] = None  # "auto" | "Beginner" | "Intermediate" | "Advanced"


class SubjectAreaCreate(BaseModel):
    name: str


# ── Auth ───────────────────────────────────────────────────────────────────

def verify_admin(x_admin_key: str = Header(None)):
    admin_key = os.getenv("ADMIN_KEY", "")
    if admin_key and x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


# ── Core generation logic ──────────────────────────────────────────────────

async def run_daily_generation(model: str = None) -> dict:
    """Generate today's topic and send notifications. Skips if topic already exists."""
    from backend.database import SessionLocal

    db = SessionLocal()
    try:
        today = date.today().isoformat()

        existing = db.query(Topic).filter(Topic.date == today).first()
        if existing:
            logger.info(f"Topic already exists for {today}, skipping")
            return {"skipped": True, "topic_id": existing.id}

        all_topics = db.query(Topic).order_by(Topic.date.desc()).all()
        previous_titles = [t.title for t in all_topics]
        subject_areas = [s.name for s in db.query(SubjectArea).order_by(SubjectArea.name).all()]

        cfg = get_llm_config()
        difficulty_mode = cfg.get("difficulty_mode", "auto")
        if difficulty_mode in DIFFICULTY_LEVELS:
            target_difficulty = difficulty_mode
        else:
            recent_difficulties = [t.difficulty for t in all_topics[:9]]
            target_difficulty = compute_target_difficulty(recent_difficulties)

        topic_data = generate_topic(today, previous_titles, model=model, subject_areas=subject_areas, target_difficulty=target_difficulty)

        new_topic = Topic(
            date=today,
            title=topic_data["title"],
            tldr=topic_data.get("tldr"),
            domain=topic_data["domain"],
            difficulty=topic_data["difficulty"],
            problem_statement=topic_data["problem_statement"],
            context_text=topic_data["context_text"],
            deep_dive=topic_data["deep_dive"],
            real_world_examples=topic_data["real_world_examples"],
            solution_approaches=topic_data["solution_approaches"],
            key_takeaways=topic_data["key_takeaways"],
            further_reading=topic_data["further_reading"],
        )
        db.add(new_topic)
        db.commit()
        db.refresh(new_topic)

        logger.info(f"Topic saved: '{new_topic.title}' (ID: {new_topic.id})")

        subscriptions = db.query(PushSubscription).all()
        push_success = 0
        stale_ids = []
        for sub in subscriptions:
            try:
                ok = send_push_notification(
                    subscription_info={"endpoint": sub.endpoint, "p256dh": sub.p256dh, "auth": sub.auth},
                    title="Today's SysDesign Topic",
                    body=new_topic.title,
                    url=f"/?topic={new_topic.id}",
                )
                if ok:
                    push_success += 1
            except Exception as e:
                logger.warning(f"Push failed for sub {sub.id}: {e}, marking stale")
                stale_ids.append(sub.id)

        for sid in stale_ids:
            db.query(PushSubscription).filter(PushSubscription.id == sid).delete()
        db.commit()

        await send_topic_email(topic_data, today)

        return {"skipped": False, "topic_id": new_topic.id, "push_sent": push_success}

    finally:
        db.close()


# ── Stats ──────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    today = date.today().isoformat()
    today_topic = db.query(Topic).filter(Topic.date == today).first()
    cfg = get_llm_config()
    return {
        "topic_count": db.query(Topic).count(),
        "subscriber_count": db.query(PushSubscription).count(),
        "today_exists": today_topic is not None,
        "today_title": today_topic.title if today_topic else None,
        "current_model": cfg["model"],
    }


# ── Topic management ───────────────────────────────────────────────────────

@router.get("/topics", response_model=list[TopicListItem])
def list_topics_admin(db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    from sqlalchemy import desc
    return db.query(Topic).order_by(desc(Topic.date)).all()


@router.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    deleted = db.query(Topic).filter(Topic.id == topic_id).delete()
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"success": True}


# ── LLM config ─────────────────────────────────────────────────────────────

@router.get("/config")
def get_config(x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    return get_llm_config()


@router.post("/config")
def set_config(body: ConfigRequest, x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    update_llm_config(body.model_dump(exclude_none=False))
    return get_llm_config()


# ── Subject areas ─────────────────────────────────────────────────────────

@router.get("/subject-areas")
def list_subject_areas(db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    return db.query(SubjectArea).order_by(SubjectArea.name).all()


@router.post("/subject-areas", status_code=201)
def add_subject_area(body: SubjectAreaCreate, db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    existing = db.query(SubjectArea).filter(SubjectArea.name == name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Subject area already exists")
    area = SubjectArea(name=name)
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.delete("/subject-areas/{area_id}")
def delete_subject_area(area_id: int, db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    deleted = db.query(SubjectArea).filter(SubjectArea.id == area_id).delete()
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Subject area not found")
    return {"success": True}


# ── Model list ─────────────────────────────────────────────────────────────

@router.get("/models")
def list_models(x_admin_key: str = Header(None)):
    """Fetch available models from Groq API."""
    verify_admin(x_admin_key)
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")
    try:
        resp = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        models = sorted(m["id"] for m in data.get("data", []))
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch models: {e}")


# ── Generation triggers ────────────────────────────────────────────────────

@router.post("/trigger", response_model=GenerateResponse)
async def trigger_generation(
    body: TriggerRequest = TriggerRequest(),
    db: Session = Depends(get_db),
    x_admin_key: str = Header(None),
):
    verify_admin(x_admin_key)
    today = date.today().isoformat()
    try:
        result = await run_daily_generation(model=body.model)
        if result.get("skipped"):
            topic = db.query(Topic).filter(Topic.date == today).first()
            return GenerateResponse(success=True, message="Topic already exists for today", topic=topic)
        topic = db.query(Topic).filter(Topic.id == result["topic_id"]).first()
        return GenerateResponse(
            success=True,
            message=f"Topic generated — {result.get('push_sent', 0)} push notifications sent",
            topic=topic,
        )
    except Exception as e:
        logger.error(f"Topic generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-force", response_model=GenerateResponse)
async def trigger_force(
    body: TriggerRequest = TriggerRequest(),
    db: Session = Depends(get_db),
    x_admin_key: str = Header(None),
):
    """Force regenerate today's topic (deletes and recreates)."""
    verify_admin(x_admin_key)
    today = date.today().isoformat()
    db.query(Topic).filter(Topic.date == today).delete()
    db.commit()
    try:
        result = await run_daily_generation(model=body.model)
        topic = db.query(Topic).filter(Topic.id == result["topic_id"]).first()
        return GenerateResponse(success=True, message="Topic force-regenerated", topic=topic)
    except Exception as e:
        logger.error(f"Force generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── TL;DR backfill ────────────────────────────────────────────────────────

@router.post("/backfill-tldr")
async def backfill_tldr(db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    """Generate and save tldr for every topic that doesn't have one yet."""
    verify_admin(x_admin_key)
    from sqlalchemy import or_
    topics = db.query(Topic).filter(or_(Topic.tldr == None, Topic.tldr == "")).order_by(Topic.date).all()  # noqa: E711
    updated, failed = 0, []
    for topic in topics:
        try:
            tldr = generate_tldr(topic.title, topic.problem_statement, topic.solution_approaches)
            topic.tldr = tldr
            db.commit()
            updated += 1
            logger.info(f"Backfilled tldr for topic {topic.id} ({topic.title})")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate tldr for topic {topic.id}: {e}")
            failed.append({"id": topic.id, "title": topic.title, "error": str(e)})
    return {"updated": updated, "failed": failed, "total": len(topics)}


# ── Push management ────────────────────────────────────────────────────────

@router.post("/push/test")
def test_push(db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    verify_admin(x_admin_key)
    subscriptions = db.query(PushSubscription).all()
    sent = 0
    for sub in subscriptions:
        try:
            ok = send_push_notification(
                subscription_info={"endpoint": sub.endpoint, "p256dh": sub.p256dh, "auth": sub.auth},
                title="Test Notification",
                body="daily_learning — admin test push",
                url="/",
            )
            if ok:
                sent += 1
        except Exception:
            pass
    return {"success": True, "message": f"Test push sent to {sent}/{len(subscriptions)} subscribers"}


@router.post("/push/cleanup")
def cleanup_subscriptions(db: Session = Depends(get_db), x_admin_key: str = Header(None)):
    """Send a test push to each subscriber; remove those that return 404/410."""
    verify_admin(x_admin_key)
    subscriptions = db.query(PushSubscription).all()
    stale_ids = []
    for sub in subscriptions:
        try:
            send_push_notification(
                subscription_info={"endpoint": sub.endpoint, "p256dh": sub.p256dh, "auth": sub.auth},
                title="Subscription check",
                body="daily_learning — verifying subscription",
                url="/",
            )
        except Exception:
            stale_ids.append(sub.id)
    for sid in stale_ids:
        db.query(PushSubscription).filter(PushSubscription.id == sid).delete()
    db.commit()
    return {"success": True, "removed": len(stale_ids), "remaining": len(subscriptions) - len(stale_ids)}


# ── VAPID ──────────────────────────────────────────────────────────────────

@router.get("/generate-vapid")
def generate_vapid(x_admin_key: str = Header(None)):
    """One-time endpoint to generate VAPID keys. Store output in env vars."""
    verify_admin(x_admin_key)
    from backend.push_service import generate_vapid_keys
    private_key, public_key = generate_vapid_keys()
    return {
        "VAPID_PRIVATE_KEY": private_key,
        "VAPID_PUBLIC_KEY": public_key,
        "note": "Store these as environment variables. Do not call this again.",
    }
