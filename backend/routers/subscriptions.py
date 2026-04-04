from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import PushSubscription
from backend.schemas import PushSubscriptionCreate, PushSubscriptionResponse, VapidPublicKeyResponse
from backend.push_service import get_vapid_keys
import os

router = APIRouter(prefix="/api/push", tags=["push"])


@router.get("/vapid-key", response_model=VapidPublicKeyResponse)
def get_vapid_public_key():
    _, public_key = get_vapid_keys()
    if not public_key:
        raise HTTPException(status_code=503, detail="Push notifications not configured")
    return {"public_key": public_key}


@router.post("/subscribe", response_model=PushSubscriptionResponse)
def subscribe(sub: PushSubscriptionCreate, db: Session = Depends(get_db)):
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == sub.endpoint
    ).first()

    if existing:
        # Update keys in case they changed
        existing.p256dh = sub.p256dh
        existing.auth = sub.auth
        db.commit()
        db.refresh(existing)
        return existing

    new_sub = PushSubscription(
        endpoint=sub.endpoint,
        p256dh=sub.p256dh,
        auth=sub.auth,
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


@router.delete("/unsubscribe")
def unsubscribe(endpoint: str, db: Session = Depends(get_db)):
    sub = db.query(PushSubscription).filter(
        PushSubscription.endpoint == endpoint
    ).first()
    if sub:
        db.delete(sub)
        db.commit()
    return {"success": True}
