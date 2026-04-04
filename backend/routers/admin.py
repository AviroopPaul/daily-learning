import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Topic, PushSubscription
from backend.schemas import GenerateResponse
from backend.llm import generate_topic
from backend.email_service import send_topic_email
from backend.push_service import send_push_notification
import os

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)


def verify_admin(x_admin_key: str = Header(None)):
    admin_key = os.getenv("ADMIN_KEY", "")
    if admin_key and x_admin_key != admin_key:
        raise HTTPException(status_code=401, detail="Unauthorized")


async def run_daily_generation() -> dict:
    """Core logic for generating today's topic and sending notifications."""
    from backend.database import SessionLocal

    db = SessionLocal()
    try:
        today = date.today().isoformat()

        # Check if already generated today
        existing = db.query(Topic).filter(Topic.date == today).first()
        if existing:
            logger.info(f"Topic already exists for {today}, skipping generation")
            return {"skipped": True, "topic_id": existing.id}

        # Fetch all previous topic titles to avoid duplication
        previous_titles = [t.title for t in db.query(Topic.title).all()]

        # Generate new topic
        topic_data = generate_topic(today, previous_titles)

        # Save to DB
        new_topic = Topic(
            date=today,
            title=topic_data["title"],
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

        # Send push notifications
        subscriptions = db.query(PushSubscription).all()
        push_success = 0
        stale_ids = []
        for sub in subscriptions:
            try:
                ok = send_push_notification(
                    subscription_info={"endpoint": sub.endpoint, "p256dh": sub.p256dh, "auth": sub.auth},
                    title=f"📐 Today's SysDesign Topic",
                    body=new_topic.title,
                    url=f"/?topic={new_topic.id}",
                )
                if ok:
                    push_success += 1
            except Exception as e:
                logger.warning(f"Push failed for sub {sub.id}: {e}, marking as stale")
                stale_ids.append(sub.id)

        # Remove stale subscriptions
        for sid in stale_ids:
            db.query(PushSubscription).filter(PushSubscription.id == sid).delete()
        db.commit()

        # Send email
        await send_topic_email(topic_data, today)

        return {
            "skipped": False,
            "topic_id": new_topic.id,
            "push_sent": push_success,
        }

    finally:
        db.close()


@router.post("/trigger", response_model=GenerateResponse)
async def trigger_generation(
    db: Session = Depends(get_db),
    x_admin_key: str = Header(None),
):
    verify_admin(x_admin_key)
    today = date.today().isoformat()

    try:
        result = await run_daily_generation()
        if result.get("skipped"):
            topic = db.query(Topic).filter(Topic.date == today).first()
            return GenerateResponse(
                success=True,
                message="Topic already exists for today",
                topic=topic,
            )

        topic = db.query(Topic).filter(Topic.id == result["topic_id"]).first()
        return GenerateResponse(
            success=True,
            message=f"Topic generated and {result.get('push_sent', 0)} push notifications sent",
            topic=topic,
        )
    except Exception as e:
        logger.error(f"Topic generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-force", response_model=GenerateResponse)
async def trigger_force(
    db: Session = Depends(get_db),
    x_admin_key: str = Header(None),
):
    """Force regenerate today's topic (overwrites existing)."""
    verify_admin(x_admin_key)
    today = date.today().isoformat()

    # Delete existing today's topic if any
    db.query(Topic).filter(Topic.date == today).delete()
    db.commit()

    try:
        result = await run_daily_generation()
        topic = db.query(Topic).filter(Topic.id == result["topic_id"]).first()
        return GenerateResponse(
            success=True,
            message="Topic force-regenerated",
            topic=topic,
        )
    except Exception as e:
        logger.error(f"Force generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
