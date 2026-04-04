# Daily Learning

One system design concept, every day. Covers real-world challenges from companies like Netflix, Google, OpenAI, and Uber — with deep dives, examples, and solutions.

Topics are AI-generated daily at **9PM IST** and delivered via browser push notification and email.

**Live:** https://daily-learning-taxnvq53va-uc.a.run.app

---

## What's inside

- **Backend** — Python FastAPI, SQLite, APScheduler
- **Frontend** — React SPA (dark/light mode, mobile-first)
- **LLM** — GROQ API (`gpt-oss-120b`) with strict structured output
- **Notifications** — Browser push (Web Push API) + HTML email
- **Deploy** — Single Docker image on Cloud Run (`my-stuff-ai`, `us-central1`)

---

## Quick start

```bash
git clone https://github.com/AviroopPaul/daily-learning
cd daily-learning
cp .env.example .env
# fill in .env
docker compose up --build
```

App runs at **http://localhost:8080**.

Generate your first topic manually:

```bash
curl -X POST http://localhost:8080/api/admin/trigger \
  -H "X-Admin-Key: your-secret-key-here"
```

---

## Environment variables

### GROQ API key (required)

1. Go to **https://console.groq.com**
2. **API Keys** → **Create API Key** (starts with `gsk_`)

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=gpt-oss-120b
```

---

### Email (optional)

Gmail recommended. Uses an App Password — not your regular password.

1. Enable **2-Step Verification** at https://myaccount.google.com/security
2. Create an App Password at https://myaccount.google.com/apppasswords
3. Copy the 16-character password

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=you@gmail.com
```

---

### Browser push notifications (optional)

VAPID keys are generated once via a built-in endpoint.

```bash
# 1. Start the app first
docker compose up --build

# 2. Generate keys
curl http://localhost:8080/api/admin/generate-vapid \
  -H "X-Admin-Key: your-secret-key-here"

# 3. Paste VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY into .env, then restart
docker compose down && docker compose up --build
```

The same key pair works in all environments — local and Cloud Run.

---

### Full `.env` reference

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=gpt-oss-120b

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=you@gmail.com

VAPID_PRIVATE_KEY=
VAPID_PUBLIC_KEY=
VAPID_EMAIL=mailto:you@gmail.com

APP_URL=http://localhost:8080
ADMIN_KEY=your-secret-key-here
DATABASE_URL=sqlite:////app/data/topics.db
```

---

## Admin endpoints

All require `X-Admin-Key` header (if `ADMIN_KEY` is set).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/trigger` | Generate today's topic (skips if already done) |
| `POST` | `/api/admin/trigger-force` | Regenerate today's topic, overwriting existing |
| `GET`  | `/api/admin/generate-vapid` | Generate VAPID key pair (run once) |
| `GET`  | `/api/health` | Health check |

---

## Deploying to Cloud Run

### Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Cloud Run and Cloud Build APIs enabled — no Artifact Registry setup needed

### Deploy

No Artifact Registry setup needed. `gcloud run deploy --source` handles the build and image storage automatically via Cloud Build.

```bash
gcloud builds submit --config cloudbuild.yaml \
  --project=my-stuff-ai \
  --substitutions \
    "_GROQ_API_KEY=gsk_xxx,\
    _SMTP_USER=you@gmail.com,\
    _SMTP_PASSWORD=xxxx xxxx xxxx xxxx,\
    _EMAIL_TO=you@gmail.com,\
    _VAPID_PRIVATE_KEY=abc...,\
    _VAPID_PUBLIC_KEY=xyz...,\
    _ADMIN_KEY=your-secret-key"
```

Or set the substitution variables as **Cloud Build trigger variables** in the console to avoid passing them every time.

### Scheduler note

`cloudbuild.yaml` sets `--min-instances=1` so APScheduler stays alive. To run at zero cost instead, create a **Cloud Scheduler** job:

```
Schedule:  30 15 * * *   (15:30 UTC = 9PM IST)
URL:       https://daily-learning-taxnvq53va-uc.a.run.app/api/admin/trigger
Method:    POST
Header:    X-Admin-Key: your-secret-key
```

---

## Local development (without Docker)

```bash
# Backend
pip install -r backend/requirements.txt
export $(grep -v '^#' .env | xargs)
PYTHONPATH=. uvicorn backend.main:app --reload --port 8080

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
# proxies /api → localhost:8080, hot reload on :5173
```

---

## Data persistence

SQLite at `/app/data/topics.db`, backed by Docker named volume `sysdesign-data`. Persists across rebuilds. Lost on `docker compose down -v`.
