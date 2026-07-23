# Deploying to Google Cloud Run (via GitHub)

This walks through getting the project on GitHub, then deployed to Cloud
Run, with Firestore wired up using Cloud Run's built-in credentials (no key
file to manage or leak).

## 0. Prerequisites
- A GitHub account
- A Google Cloud account (free tier is enough — Cloud Run has a generous
  free monthly quota, you're unlikely to be charged for a small demo project)
- `git` and the `gcloud` CLI installed on your machine
  (install gcloud: https://cloud.google.com/sdk/docs/install)

## 1. Push the project to GitHub

```bash
cd seo-gap-analyzer
git init
git add .
git commit -m "SEO content gap analyzer - FastAPI + Firestore"
```

Create a new empty repo on github.com (no README/license, so it doesn't
conflict), then:

```bash
git remote add origin https://github.com/<your-username>/seo-gap-analyzer.git
git branch -M main
git push -u origin main
```

## 2. Create a GCP project and enable the right APIs

```bash
gcloud auth login
gcloud projects create seo-gap-analyzer-demo --set-as-default
gcloud config set project seo-gap-analyzer-demo

gcloud services enable run.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## 3. Create the Firestore database (one-time, per project)

```bash
gcloud firestore databases create --location=us-central1
```

(Pick any region close to you — this doesn't have to match Cloud Run's region.)

## 4. Deploy to Cloud Run directly from source

You don't need to build the Docker image yourself — `gcloud run deploy` reads
the Dockerfile and builds it for you via Cloud Build.

```bash
gcloud run deploy seo-gap-analyzer \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_FIRESTORE=true
```

- `--allow-unauthenticated` makes the URL publicly reachable — fine for a
  demo project, but note it means anyone with the link can hit the API.
- `--set-env-vars USE_FIRESTORE=true` tells the app to use real Firestore
  via Cloud Run's built-in service account credentials — no key file needed,
  because Cloud Run's default service account already has access to
  Firestore in the same project.
- If you want real LLM calls (not the mock fallback), add
  `,OPENAI_API_KEY=sk-...` to that same `--set-env-vars` flag. Better: use
  `gcloud run deploy --update-secrets` with Secret Manager instead of a
  plain env var, so the key isn't sitting in your deploy command / shell
  history in plaintext.

When it finishes, `gcloud` prints a live URL like:
`https://seo-gap-analyzer-xxxxx-uc.a.run.app`

## 5. Verify it's live

```bash
curl -X POST https://<your-cloud-run-url>/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "This article explains what a CDN is.", "target_keyword": "best CDN for small business"}'
```

You should get back the same structured JSON you saw locally — and this
time, if `USE_FIRESTORE=true`, the result is actually saved in Firestore.
Check it in the Firebase console: https://console.firebase.google.com →
your project → Firestore Database → `analyses` collection.

## 6. Put the live URL to use

- Add it to your GitHub repo's README and description
- Drop the link in your Adaptify application follow-up, or keep it ready
  for interview conversation ("here's a live version, backed by real
  Firestore, deployed on Cloud Run")
- `/docs` on the live URL gives anyone an interactive API playground —
  worth linking directly (e.g. `https://<your-url>/docs`)

## Cost note
Cloud Run and Firestore both have free tiers generous enough that a small
demo project like this should cost close to $0/month. Set a billing budget
alert in the GCP console if you want peace of mind either way.
