# Daily Learning

One system design concept, every day. Deep dives, real-world examples, and solutions — AI-generated at **9PM IST** and delivered via push notification and email.

**Live:** https://daily-learning-taxnvq53va-uc.a.run.app

---

## Stack

- **Backend** — FastAPI, SQLite, APScheduler
- **Frontend** — React SPA (dark/light, mobile-first)
- **LLM** — GROQ `gpt-oss-120b` with strict structured output
- **TTS** — Google Cloud WaveNet (4M chars/month free)
- **Notifications** — Browser push + HTML email
- **Deploy** — Cloud Run (`my-stuff-ai`, `us-central1`)
- **Chrome Extension** — YouTube blocker + quiz nudges (`/chrome-extension`)

---

## Quick start

```bash
git clone https://github.com/AviroopPaul/daily-learning
cd daily-learning
cp .env.example .env   # fill in values
docker compose up --build
```

App runs at **http://localhost:8080**. Generate your first topic:

```bash
curl -X POST http://localhost:8080/api/admin/trigger \
  -H "X-Admin-Key: your-secret-key-here"
```

---

## Environment variables

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=gpt-oss-120b

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=you@gmail.com

VAPID_PRIVATE_KEY=        # generate via GET /api/admin/generate-vapid
VAPID_PUBLIC_KEY=
VAPID_EMAIL=mailto:you@gmail.com

GOOGLE_TTS_API_KEY=       # restricted to texttospeech.googleapis.com

APP_URL=http://localhost:8080
ADMIN_KEY=your-secret-key-here
DATABASE_URL=sqlite:////app/data/topics.db
```

---

## Chrome Extension

Blocks YouTube until today's quiz is done. Sends nudge notifications at 9AM, 12PM, 6PM.

1. `chrome://extensions` → Enable **Developer mode** → **Load unpacked** → select `chrome-extension/`
2. Or download the latest zip from the [Releases page](https://github.com/AviroopPaul/daily-learning/releases)

---

## Admin endpoints

All require `X-Admin-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/trigger` | Generate today's topic (skips if exists) |
| `POST` | `/api/admin/trigger-force` | Regenerate today's topic, overwriting existing |
| `POST` | `/api/admin/quiz/generate/{topic_id}` | Generate quiz for a specific topic |
| `POST` | `/api/admin/quiz/backfill` | Backfill quizzes for all topics |
| `GET`  | `/api/admin/generate-vapid` | Generate VAPID key pair (run once) |
| `GET`  | `/api/health` | Health check |

---

## Local dev (without Docker)

```bash
# Backend
pip install -r backend/requirements.txt
export $(grep -v '^#' .env | xargs)
PYTHONPATH=. uvicorn backend.main:app --reload --port 8080

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```
