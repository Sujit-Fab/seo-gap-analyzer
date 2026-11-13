---
name: seo-gap-analyzer
description: Compare a page or draft against the pages that actually rank for a target keyword and report the topics it is missing, with priorities and concrete additions. Use when the user asks for an SEO content gap analysis, asks why a page is not ranking for a keyword, or wants to know what to add to an article to compete for a keyword.
---

# SEO Content Gap Analyzer

Find what a piece of content is missing compared with the pages that currently
rank for its target keyword. Every gap you report must be traceable to a real
competitor page you read in this session.

## Inputs

Collect these before starting. Ask once if either is missing.

1. **Content** - one of:
   - a URL (fetch it and use the main article text), or
   - a local file path (read it), or
   - text pasted by the user.
2. **Target keyword** - the search query the content should rank for.

Optional: target country/language (default: United States, English) and the
number of competitors to compare (default 5, maximum 10).

Stop and tell the user if the content is under about 20 words; there is nothing
to analyze.

## Step 1 - Get the real search results

Find the pages that rank for the target keyword.

- If a SERP data tool is available (for example a DataForSEO organic results
  tool), use it with the keyword, country and language. Make ONE call.
- Otherwise use the agent's web search tool with the exact keyword.
- If neither is available, go to "No search access" below.

Keep the top organic results only. Drop ads, the user's own domain, video and
image results, forums, and marketplaces/directories unless they dominate the
results (in which case say so in the assessment, because it signals search
intent the content may not match).

Then clean the list before reading anything:

- **One page per domain.** If a domain appears more than once, keep its
  highest result and drop the rest. Count the dropped duplicates and report
  them under "Skipped".
- **Country.** A SERP data tool returns results for the requested country. A
  general web search tool does not. When using general web search, prefer
  results that target the requested country; if you must include a page aimed
  at another country to reach N competitors, mark its country in the
  competitors table.
- **Rank source.** Record whether the order came from a SERP data tool
  (`serp_tool`) or from general web search (`web_search`). Web search order is
  not the search engine's real ranking, and the report must say so.

## Step 2 - Read the competitors

Fetch the top N competitor pages. For each one, record:

- URL and title
- the H1/H2/H3 outline
- notable elements: comparison tables, pricing, FAQs, step-by-step sections,
  statistics, original data, tools/calculators, images or diagrams
- approximate word count

If a page cannot be fetched (blocked, paywalled, empty), skip it and move to
the next result. Do not guess its contents. If fewer than 3 competitors could
be read, say so plainly in the assessment.

Also skip a page, and move to the next result, when it is low quality:

- thin or auto-generated content (for example a page whose product names,
  prices or statistics cannot be matched to any real brand or source)
- a near-copy of a page you have already read
- a page that is only a product listing or category page with no article

Say which pages were skipped for quality and why. A weak page that still
ranks is a signal about the keyword's difficulty; mention that in the summary
instead of treating the page as a competitor to imitate.

For long pages, the outline plus the first sentences under each heading is
enough. Do not paste competitor text into the report.

For every topic you record, note where on the page it appears (the heading it
sits under). You will need this for the "Where to check" column.

## Step 3 - Find the gaps

Build a list of topics covered by the competitors and mark which ones the
user's content covers.

A topic is a **gap** when at least 2 competitors cover it and the user's
content does not, or covers it only in passing.

Assign priority by evidence, not opinion:

- **high** - covered by most competitors read (more than half), or it is what
  the keyword's search intent directly asks for
- **medium** - covered by 2 or more competitors, but fewer than half
- **low** - covered by 1 competitor, but clearly useful to the reader

Also note the reverse: anything the user's content covers that no competitor
does. That is a strength to keep, not a gap.

## Step 4 - Report

Give the report in this order.

**1. Summary** - two or three sentences: how the content compares overall and
the single most important thing to fix.

**2. Competitors analyzed** - a table: rank, title, URL, country (if not the
requested one), word count. Under the table, state the rank source in one
line: either "Ranks from live SERP data for <country>" or "Order from general
web search; not the search engine's actual ranking and not country-specific."
Then list pages that were skipped and why (duplicate domain, could not be
fetched, low quality).

**3. Gaps** - a table sorted high to low:

| Priority | Missing topic | Why it matters | Covered by | Where to check |
|---|---|---|---|---|

"Covered by" lists the competitor ranks that cover the topic, e.g. `#1, #2, #4`.
"Where to check" names one competitor and the heading the topic sits under,
e.g. `#5, "Our Office Camera Picks"`, so the reader can open the page and
confirm it. Prefer a competitor whose page loaded without restrictions.

Any specific figure taken from a competitor (a price, a number of days, a
count) must appear with the competitor it came from. If only one competitor
states it, say so.

**4. Suggested additions** - a short numbered list of concrete edits, each one
specific enough to act on ("Add an H2 'Pricing' with a 3-row plan comparison
table", not "Improve pricing coverage").

**5. Strengths to keep** - what the content has that competitors lack.

If the user asks for machine-readable output, also return this JSON:

```json
{
  "target_keyword": "string",
  "data_source": "serp" | "model_estimate",
  "rank_source": "serp_tool" | "web_search" | null,
  "overall_assessment": "string",
  "competitors": [
    {"rank": 1, "url": "string", "title": "string", "country": "string", "word_count": 0}
  ],
  "skipped": [
    {"url": "string", "reason": "duplicate_domain" | "fetch_failed" | "low_quality"}
  ],
  "gaps": [
    {
      "topic": "string",
      "why_it_matters": "string",
      "priority": "high" | "medium" | "low",
      "covered_by": [1, 2],
      "where_to_check": "string"
    }
  ],
  "suggested_additions": ["string"],
  "strengths": ["string"]
}
```

## No search access

If you cannot retrieve search results or competitor pages, do not present a
normal report. Tell the user that live data was unavailable, then offer an
estimate based on general knowledge of the topic. Label that report
"Estimate - not based on live search results", set `data_source` to
`model_estimate`, set `rank_source` to null, leave `competitors` empty and
leave "Covered by" and "Where to check" blank.

## Rules

- Never invent a competitor, a URL, a ranking position or a statistic.
- Every gap with `data_source: serp` must name the competitors that cover it.
- Do not recommend keyword stuffing, hidden text, or copying competitor wording.
- Report on the content as it is. Do not rewrite it unless the user asks.
- Word counts are estimates; label them "approx."
- Keep tool use small: one SERP call, at most 10 page fetches.
