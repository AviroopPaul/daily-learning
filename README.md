# Daily Learning

One system design concept, every day. Covers real-world challenges from companies like Netflix, Google, OpenAI, and Uber — with deep dives, examples, and solutions.

Topics are AI-generated daily at **9PM IST** and delivered via browser push notification and email.

**Live:** https://daily-learning-taxnvq53va-uc.a.run.app

---

## What's inside

- **Backend** — Python FastAPI, SQLite, APScheduler
- **Frontend** — React SPA (dark/light mode, mobile-first, font scaling)
- **LLM** — GROQ API (`gpt-oss-120b`) with strict structured output
- **Notifications** — Browser push (Web Push API) + HTML email
- **Deploy** — Single Docker image on Cloud Run (`my-stuff-ai`, `us-central1`)
- **Chrome Extension** — YouTube blocker + daily quiz nudges (`/chrome-extension`)

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

## Chrome Extension

The `chrome-extension/` folder contains a Manifest V3 extension that:
- **Blocks YouTube** until you submit today's quiz
- Sends **nudge notifications** at 9AM, 12PM and 6PM if the quiz isn't done
- Shows a **popup** with your quiz status and current streak

### Loading the extension (dev / sideload)

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (toggle, top-right)
3. Click **Load unpacked** → select the `chrome-extension/` folder
4. Pin the **Daily Learning Quiz Guard** icon from the toolbar

### Installing from a release

Every merge to `main` automatically publishes a GitHub Release with a zipped extension.

1. Go to the [Releases page](https://github.com/AviroopPaul/daily-learning/releases)
2. Download `daily-learning-quiz-guard-vX.X.X.zip`
3. Unzip, then follow the **Load unpacked** steps above

> **Bumping the version:** Edit `"version"` in `chrome-extension/manifest.json` before merging — the release workflow reads that value for the tag and zip filename. Merging without bumping the version will skip the release (tag already exists).

---

## Admin endpoints

All require `X-Admin-Key` header (if `ADMIN_KEY` is set).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/trigger` | Generate today's topic + quiz (skips if already done) |
| `POST` | `/api/admin/trigger-force` | Regenerate today's topic + quiz, overwriting existing |
| `POST` | `/api/admin/quiz/generate/{topic_id}` | Generate quiz for a specific topic |
| `POST` | `/api/admin/quiz/backfill` | Generate quizzes for all topics that don't have one |
| `GET`  | `/api/admin/generate-vapid` | Generate VAPID key pair (run once) |
| `GET`  | `/api/health` | Health check |

---

## Deploying to Cloud Run

See [DEPLOYMENT.md](DEPLOYMENT.md).

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

**On Cloud Run**, the database file lives in the GCS bucket `my-stuff-ai-db-data`, mounted at `/app/data` via a Cloud Run volume. The SQLite file persists across deployments automatically — no action needed for schema changes since the app uses `Base.metadata.create_all` on startup (adds new tables, never drops existing ones).
