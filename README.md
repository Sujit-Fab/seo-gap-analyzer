# SEO Content Gap Analyzer

🔗 **Live demo:** https://seo-gap-analyzer-987224764162.us-central1.run.app/docs
📦 **Code:** https://github.com/Sujit-Fab/seo-gap-analyzer

A small FastAPI service that takes a piece of content and a target keyword,
uses a real LLM (OpenAI GPT-5.6 Sol) to identify what topics/angles are
missing compared to what a well-ranking page would cover, and returns a
structured (Pydantic-validated) gap analysis. Results are saved to Firestore
so they can be looked up later.

Built as a hands-on practice project to get comfortable with Python, FastAPI,
and Firebase ahead of applying to AI-native, SEO-focused engineering roles —
and then deployed live end-to-end on Google Cloud Run.

## Try it yourself — no setup required

1. Open the [live docs](https://seo-gap-analyzer-987224764162.us-central1.run.app/docs)
2. Expand **POST /analyze** → click "Try it out"
3. Paste in any content + a target keyword → click "Execute"
4. Get back a real, structured SEO gap analysis in seconds

## Live infrastructure

- **API:** deployed on **Google Cloud Run**, built directly from this repo's `Dockerfile`
- **LLM:** real calls to **OpenAI's GPT-5.6 Sol**, requesting strict JSON output validated against a Pydantic schema before it's ever returned to a client
- **Storage:** results persisted in **Firestore**, using Cloud Run's built-in service account credentials (no key file to manage)
- **Secrets:** the OpenAI API key is stored in **Google Secret Manager**, not as a plaintext environment variable

## Why this shape

- **Structured output from an LLM, validated before it leaves the API** —
  the same pattern I used in an earlier Next.js/Supabase project, ported to
  Python: ask the model for strict JSON matching a known schema, then
  validate with Pydantic rather than trusting raw model output.
- **Runs with zero setup locally, too.** No `OPENAI_API_KEY`? It falls back
  to a local mock analysis with the same shape. No Firebase credentials? It
  falls back to a local JSON file with the same read/write interface. Swap
  in real credentials and the exact same code talks to the real services —
  nothing else changes. That's exactly what happened going from local dev
  to this live deployment.

## Run it locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive API docs, or:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "This article explains what a CDN is and why sites use one.", "target_keyword": "best CDN for small business"}'
```

## Run the tests

```bash
pytest tests/ -v
```

All 5 tests run against the local mock/fallback paths, so they pass with no
external credentials.

## Deploy it yourself

See [`DEPLOY.md`](./DEPLOY.md) for the full step-by-step guide to deploying
this to Google Cloud Run with Firestore and Secret Manager wired in.

## Going further (not built yet)

- Real Firestore integration test (currently only unit-tested against the
  local fallback)
- Retry-with-stricter-prompt if the LLM ever returns invalid JSON
- Auth / rate limiting on the public endpoints
- Cost tracking on the OpenAI calls
