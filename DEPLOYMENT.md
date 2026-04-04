# Deployment

**Live:** https://daily-learning-taxnvq53va-uc.a.run.app
**GCP project:** `my-stuff-ai` · **Region:** `us-central1` · **Service:** `daily-learning`

---

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Cloud Run and Cloud Build APIs enabled — no Artifact Registry setup needed

---

## Deploy

`cloudbuild.yaml` uses `gcloud run deploy --source` — Cloud Build handles the image build and storage automatically. No Artifact Registry repo to manage.

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

---

## Scheduler note

`cloudbuild.yaml` sets `--min-instances=1` so APScheduler stays alive inside the container. To run at zero idle cost instead, set `--min-instances=0` and create a **Cloud Scheduler** job:

```
Schedule:  30 15 * * *   (15:30 UTC = 9PM IST)
URL:       https://daily-learning-taxnvq53va-uc.a.run.app/api/admin/trigger
Method:    POST
Header:    X-Admin-Key: your-secret-key
```
