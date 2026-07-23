# SEO Content Gap Analyzer

A small FastAPI service that takes a piece of content and a target keyword,
asks an LLM what topics/angles are missing compared to what a well-ranking
page would cover, and returns a structured (Pydantic-validated) gap analysis.
Results are saved to Firestore (or a local file if you don't have Firebase
credentials handy) so they can be looked up later.

Built as a practice project to get hands-on with Python/FastAPI/Firebase
ahead of applying to AI-native, SEO-focused engineering roles.

## Why this shape

- **Structured output from an LLM, validated before it leaves the API** —
  same pattern I used in an earlier Next.js/Supabase project, ported to
  Python: ask the model for strict JSON matching a known schema, then
  validate with Pydantic rather than trusting raw model output.
- **Runs with zero setup.** No `OPENAI_API_KEY`? It falls back to a local
  mock analysis with the same shape. No Firebase credentials? It falls back
  to a local JSON file with the same read/write interface. Swap in real
  credentials and the exact same code talks to the real services — nothing
  else changes.

## Run it

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

## Going further (not built yet)

- Real Firestore integration test (currently only unit-tested against the
  local fallback)
- Retry-with-stricter-prompt if the LLM ever returns invalid JSON
- Auth on the endpoints
- Rate limiting / cost tracking on the OpenAI calls
