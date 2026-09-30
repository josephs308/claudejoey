# AEO / GEO: getting cited by AI answer engines

AEO (answer engine optimization, also called GEO — generative engine optimization) is about being the source ChatGPT, Perplexity, Claude, Copilot, Gemini and Google's AI Overviews quote or name when someone asks a question. It builds on normal SEO — these systems mostly retrieve from search indexes (Bing for ChatGPT search and Copilot, Google for AI Overviews and Gemini, their own crawlers for others) — then pick passages that answer the question cleanly.

## Contents
1. Let the crawlers in
2. Write quotable passages
3. Structure pages for extraction
4. Entity consistency and authority
5. llms.txt
6. Freshness and feeds
7. Measuring it

## 1. Let the crawlers in

- Make sure robots.txt doesn't block the bots you want. Current user agents worth knowing:
  - OpenAI: `OAI-SearchBot` (ChatGPT search results), `ChatGPT-User` (fetches when a user asks), `GPTBot` (model training)
  - Anthropic: `ClaudeBot` (training), `Claude-SearchBot` (search), `Claude-User` (user-initiated fetch)
  - Perplexity: `PerplexityBot`, `Perplexity-User`
  - Google: `Googlebot` powers Search and AI Overviews; `Google-Extended` only controls use for Gemini training/grounding outside Search — blocking it doesn't remove you from AI Overviews
  - Microsoft: `Bingbot` feeds Bing, Copilot and ChatGPT's search index
  - Apple: `Applebot`, `Applebot-Extended` (training)
- A business that wants to be recommended by AI should generally allow the search/user-fetch bots. Blocking training bots is a separate business choice; say what each one does and let the owner decide.
- Content must be in the server-rendered HTML. Many AI fetchers don't run JavaScript; text injected client-side may be invisible to them.
- **Submit to Bing Webmaster Tools.** It's the index behind ChatGPT search and Copilot, and it supports IndexNow for fast recrawls.

## 2. Write quotable passages

- **Quick answer block**: right under the H1 (or the first H2), a 40–60 word paragraph that directly answers the page's main question in a self-contained way, e.g. *"What is PPC for law firms? PPC for law firms is paid search advertising, mainly Google Search Ads, where a firm bids to appear at the top of results for searches like 'car accident lawyer near me'…"*. Start with the term being defined; no "we", no fluff, no dependence on earlier context.
- **Question-shaped H2s** that match how people ask ("How much does SEO cost for a law firm?"), each followed immediately by a direct 1–3 sentence answer, then detail.
- **Specifics beat adjectives**: numbers, ranges, timeframes, named steps, named tools, conditions ("most firms see calls within 2–4 weeks of launching LSA"). AI systems prefer passages with concrete, checkable facts — but only state facts you can stand behind.
- **Lists and tables** for steps, comparisons, pricing tiers, specs. They're easy to lift intact.
- One idea per paragraph, 40–110 words; avoid walls of text.
- Define acronyms on first use on every page (pages are read in isolation).

## 3. Structure pages for extraction

- Visible FAQ section (5–8 Q&As) with FAQPage schema using identical wording.
- Clean heading hierarchy (one H1, logical H2/H3) — it's how retrieval chunkers split pages.
- Comparison pages ("X vs Y"), pricing/cost pages, "how it works" process pages and glossary pages get cited disproportionately — create them for the questions your buyers actually ask.
- Author bylines with real credentials on articles; an About page with real people.
- Keep boilerplate (nav, cookie banners, repeated CTAs) out of the main content flow; use `<main>` and `<article>`.

## 4. Entity consistency and authority

AI systems decide "who is this business and are they credible" by cross-checking sources:
- Identical name, description, contact details and category on the site, schema, Google Business Profile, LinkedIn, directories, and review sites.
- Organization schema with `sameAs` pointing to the official profiles.
- Get mentioned on third-party sites that already rank/get cited for your topic (industry directories, "best X" roundups, podcasts, local press, Reddit/Quora answers where appropriate). Unlinked brand mentions count for AI visibility.
- A clear one-sentence description of what the business is, repeated consistently (homepage intro, About, schema `description`, llms.txt, social bios).

## 5. llms.txt

A proposed (not standardized, not required by any major engine) plain-text/markdown file at `/llms.txt` that summarizes the site for LLMs. It's cheap and harmless, so include it:

```markdown
# Brand Name

> One or two sentences: what the business is, who it serves, where.

Contact: hello@example.com. Book a call at https://example.com/contact/.

## Services

- [Service name](https://example.com/services/x/): the page's quick-answer sentence.

## Guides

- [Post title](https://example.com/blog/post/): one-line summary.
```

Generate it from the same content source as the pages so it never drifts. Serve it as `text/plain; charset=utf-8`.

## 6. Freshness and feeds

- Show and update "Last updated" dates on pages whose content really changes; keep `dateModified` in schema in sync.
- RSS/Atom feed for the blog (`<link rel="alternate" type="application/rss+xml">` in the head).
- IndexNow (Bing, Yandex, others) to ping on publish; Search Console URL Inspection → Request indexing for important new pages.

## 7. Measuring it

- Analytics: segment referral traffic from `chatgpt.com`, `perplexity.ai`, `copilot.microsoft.com`, `gemini.google.com`, `claude.ai`.
- Ask new leads "how did you hear about us?" with an "AI assistant (ChatGPT, etc.)" option.
- Periodically ask the major assistants the buyer's real questions (with location) and record whether the brand is named or cited, and which page is linked.
- Search Console includes AI Overviews/AI Mode impressions within normal Performance data (not broken out separately).
