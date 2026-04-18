import os
import base64
import logging
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()

GOOGLE_TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


class TTSRequest(BaseModel):
    text: str


@router.post("/api/tts")
async def synthesize(req: TTSRequest):
    api_key = os.getenv("GOOGLE_TTS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="TTS not configured")

    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    text = req.text.strip()

    # Google TTS v1 limit is 5000 bytes per request; chunk at sentence boundaries
    chunks = _split_text(text, max_bytes=4800)

    audio_parts: list[bytes] = []
    async with httpx.AsyncClient(timeout=30) as client:
        for chunk in chunks:
            payload = {
                "input": {"text": chunk},
                "voice": {"languageCode": "en-US", "name": "en-US-Wavenet-D"},
                "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.95},
            }
            resp = await client.post(
                GOOGLE_TTS_URL,
                params={"key": api_key},
                json=payload,
            )
            if resp.status_code != 200:
                logger.error("Google TTS error %s: %s", resp.status_code, resp.text)
                raise HTTPException(status_code=502, detail="TTS upstream error")
            audio_b64 = resp.json().get("audioContent", "")
            audio_parts.append(base64.b64decode(audio_b64))

    return Response(content=b"".join(audio_parts), media_type="audio/mpeg")


def _split_text(text: str, max_bytes: int) -> list[str]:
    """Split text into chunks that fit within max_bytes, breaking at sentence ends."""
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    chunks = []
    current = ""
    # Split on sentences (period/exclamation/question followed by space or end)
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sentence in sentences:
        candidate = (current + " " + sentence).strip() if current else sentence
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If single sentence is still too long, hard-split it
            if len(sentence.encode("utf-8")) > max_bytes:
                words = sentence.split()
                part = ""
                for word in words:
                    trial = (part + " " + word).strip() if part else word
                    if len(trial.encode("utf-8")) <= max_bytes:
                        part = trial
                    else:
                        if part:
                            chunks.append(part)
                        part = word
                current = part
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks
