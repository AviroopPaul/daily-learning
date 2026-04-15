from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TopicBase(BaseModel):
    date: str
    title: str
    domain: str
    difficulty: str
    tldr: Optional[str] = None
    problem_statement: str
    context_text: str
    deep_dive: str
    real_world_examples: str
    solution_approaches: str
    key_takeaways: list[str]
    further_reading: list[str]


class TopicCreate(TopicBase):
    pass


class TopicResponse(TopicBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TopicListItem(BaseModel):
    id: int
    date: str
    title: str
    domain: str
    difficulty: str
    created_at: datetime

    class Config:
        from_attributes = True


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateResponse(BaseModel):
    success: bool
    message: str
    topic: Optional[TopicResponse] = None


class VapidPublicKeyResponse(BaseModel):
    public_key: str
