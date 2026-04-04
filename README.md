# 📐 SysDesign Daily

One system design concept, every day. Covers real-world challenges from companies like Netflix, Google, OpenAI, and Uber — with deep dives, examples, and solutions.

Topics are AI-generated daily at **9PM IST** and delivered via browser push notification and email.

---

## What's inside

- **Backend** — Python FastAPI, SQLite, APScheduler
- **Frontend** — React SPA (dark/light mode, mobile-first)
- **LLM** — GROQ API (`gpt-oss-120b`) for daily topic generation
- **Notifications** — Browser push (Web Push API) + HTML email
- **Deploy** — Single Docker image, Cloud Run ready

---

## Quick start

### 1. Clone and configure

```bash
git clone <your-repo>
cd system-design-daily
cp .env.example .env
```

Open `.env` and fill in the values (see sections below).

### 2. Run

```bash
docker compose up --build
```

App runs at **http://localhost:8080**.

### 3. Generate your first topic

The scheduler fires automatically at 9PM IST, but you can trigger it manually:

```bash
curl -X POST http://localhost:8080/api/admin/trigger \
  -H "X-Admin-Key: your-secret-key-here"
```

---

## Environment variables

### GROQ API key (required)

GROQ provides free LLM inference. The app uses `gpt-oss-120b`.

1. Go to **https://console.groq.com**
2. Sign up / log in
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_`)

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=gpt-oss-120b
```

---

### Email (optional but recommended)

The app sends a daily HTML email at 9PM IST using SMTP. Gmail works out of the box.

**Gmail setup:**
1. Go to **https://myaccount.google.com/security**
2. Enable **2-Step Verification** (required for app passwords)
3. Go to **https://myaccount.google.com/apppasswords**
4. Create a new app password — name it anything (e.g. "SysDesign Daily")
5. Copy the 16-character password

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=you@gmail.com
```

> If you use a different provider (Outlook, Fastmail, etc.), update `SMTP_HOST` and `SMTP_PORT` accordingly.

---

### Browser push notifications (optional)

Push notifications require a VAPID key pair. Generate one using the built-in endpoint.

**Step 1** — Start the app first (even without VAPID keys set):

```bash
docker compose up --build
```

**Step 2** — Generate keys:

```bash
curl http://localhost:8080/api/admin/generate-vapid \
  -H "X-Admin-Key: your-secret-key-here"
```

Response:

```json
{
  "VAPID_PRIVATE_KEY": "abc123...",
  "VAPID_PUBLIC_KEY":  "xyz789...",
  "note": "Store these as environment variables. Do not call this again."
}
```

**Step 3** — Paste both values into `.env`:

```env
VAPID_PRIVATE_KEY=abc123...
VAPID_PUBLIC_KEY=xyz789...
VAPID_EMAIL=mailto:you@gmail.com
```

**Step 4** — Restart:

```bash
docker compose down && docker compose up --build
```

The notification bell in the app header will now be functional.

---

### Admin key

Protects the `/api/admin/*` endpoints (topic generation, force-refresh, VAPID generation). Set it to any secret string.

```env
ADMIN_KEY=your-secret-key-here
```

Leave it empty during local development if you prefer no auth.

---

### Full `.env` reference

```env
# LLM
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=gpt-oss-120b

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=you@gmail.com

# Push notifications
VAPID_PRIVATE_KEY=
VAPID_PUBLIC_KEY=
VAPID_EMAIL=mailto:you@gmail.com

# App
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
- Cloud Run, Cloud Build, and Artifact Registry APIs enabled

### One-time setup

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create sysdesign-daily \
  --repository-format=docker \
  --location=us-central1

# Connect your GitHub repo to Cloud Build
# https://console.cloud.google.com/cloud-build/triggers
```

### Deploy

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions \
    _GROQ_API_KEY="gsk_xxx",\
    _SMTP_USER="you@gmail.com",\
    _SMTP_PASSWORD="xxxx xxxx xxxx xxxx",\
    _EMAIL_TO="you@gmail.com",\
    _VAPID_PRIVATE_KEY="abc...",\
    _VAPID_PUBLIC_KEY="xyz...",\
    _ADMIN_KEY="your-secret-key"
```

Or set the substitution variables as **Cloud Build trigger variables** in the console so you don't have to pass them on every deploy.

### Keep the scheduler alive

The `cloudbuild.yaml` sets `--min-instances=1` so APScheduler keeps running. If you prefer zero idle cost, instead create a **Cloud Scheduler** job to call the trigger endpoint:

```
Frequency:  30 15 * * *   (15:30 UTC = 9PM IST)
Target:     HTTP
URL:        https://<your-service>.run.app/api/admin/trigger
Method:     POST
Headers:    X-Admin-Key: your-secret-key
```

---

## Local development (without Docker)

```bash
# Backend
pip install -r backend/requirements.txt
export $(grep -v '^#' .env | xargs)
PYTHONPATH=. uvicorn backend.main:app --reload --port 8080

# Frontend (separate terminal, hot reload)
cd frontend
npm install
npm run dev   # runs on http://localhost:5173, proxies /api to :8080
```

---

## Data persistence

Topics are stored in SQLite at `/app/data/topics.db` inside the container, backed by a Docker named volume (`sysdesign-data`). Data survives container restarts and rebuilds.

To reset all topics:

```bash
docker compose down -v   # removes the volume
docker compose up --build
```
