---
title: "Pulling reference models from Thingiverse (no official API access)"
type: procedure
beth_topics:
  - tiacad
  - thingiverse
  - validation
  - rebuild-benchmark
---

# Thingiverse Model Access (No App Registration Required)

Thingiverse's official developer API (`api.thingiverse.com` with an app-registered
OAuth token) is effectively dead — app registration is closed/broken as of 2026-07
(confirmed via the developer forums and a broken `login.makerbot.com` registration
flow). This doc records a working alternative, reverse-engineered from the live
site, for pulling STL/source files to use as real-world rebuild targets against
TiaCAD's YAML language (see [BACKLOG](../../BACKLOG.md) / validation ladder in
[MODEL_VALIDATION](MODEL_VALIDATION.md) for why: TiaCAD's Tier 0-5 corpus is all
hand-authored, so external models are a useful "does this hold up on a real part"
check).

## Why plain `curl` alone doesn't work

`www.thingiverse.com` sits behind Cloudflare's bot-challenge at the edge. Any
request without a browser-issued `cf_clearance` cookie gets served a JS challenge
page ("Just a moment...") regardless of headers, User-Agent, or auth tokens used.
This is a TLS/JS fingerprint check, not a credentials check — so raw `curl` is
blocked before it ever reaches the app layer.

**The workaround:** open the site once in a real browser (solves the Cloudflare
challenge), extract the tokens it uses for its own internal API calls via
`fetch()` executed in-page, then reuse those tokens directly with `curl` for
everything after. One of the two tokens turned out to be a static, non-expiring
value — no repeat browser visits needed for it.

## The three endpoints

All discovered by opening `thingiverse.com/search?...` and a `thing:<id>/files`
page in a browser and inspecting `performance.getEntriesByType('resource')` for
same-origin (non-ad, non-tracker) requests — the page is drowned in ad-tech
traffic, so filter to `www.thingiverse.com` / `api.thingiverse.com` explicitly.

### 1. Search

```
GET https://www.thingiverse.com/api/v2/search/things?term=<query>&page=1&per_page=20&sort=relevant
Authorization: Bearer <anonymous JWT>
```

The JWT is minted client-side, cached in `localStorage['tv_access_token']`
(`{"data": "<jwt>", "expires": "..."}`), `sub: "VIEW"` — a view-only anonymous
token. **This one expires (~24h)** and must be re-minted through the browser via:

```js
fetch('https://www.thingiverse.com/api/v2/auth/view', {credentials:'same-origin'})
  .then(r => r.json())  // → { access: "<jwt>" }
```

Response shape: `{ hits: [ { id, name, public_url, ... } ], ... }`.

### 2. File listing for a thing

```
GET https://www.thingiverse.com/api/things/<thing_id>/files
Authorization: Bearer 56edfc79ecf25922b98202dd79a291aa
```

This token is **static** — not tied to a session, not a JWT, doesn't expire on
the same clock as the search token. However this endpoint is still served through
Cloudflare like the search endpoint, so a cold `curl` (no `cf_clearance` cookie)
gets the JS-challenge page even with the correct token. Treat both
`www.thingiverse.com/api/*` paths as "needs a live/cleared browser session";
only the actual file bytes (next section) are freely curl-able.

Response is an array of file objects: `name`, `size`, `formatted_size`,
`direct_url`, `hash`, etc.

### 3. File download — plain `curl`, no auth, no Cloudflare

```
GET <direct_url>   # e.g. https://api.thingiverse.com/v2/files/109122/download?increment_download=false
```

`api.thingiverse.com` (note: different host than `www.thingiverse.com`) serves
the actual bytes with **no auth and no bot-challenge**. Verified with a cold
`curl` process. This is the only step safe to script freely/repeatedly.

## Practical recipe

1. Open a browser session once (Firefox devtools MCP tools, not Chrome) against
   `https://www.thingiverse.com/search?q=<query>&type=things` and
   `https://www.thingiverse.com/thing:<id>/files` to bootstrap tokens if you
   don't already have a fresh JWT.
2. Pull `hits[].id` from the search response for candidate things.
3. For each thing, call the files endpoint (needs the cleared browser context)
   to get `direct_url`s.
4. `curl` each `direct_url` directly — no browser needed from here.

## Known limitations

- No proof this survives Cloudflare rotating its challenge scheme or Thingiverse
  invalidating the static files-endpoint token — if step 2 starts 401ing, re-derive
  the token from a fresh browser session's network log the same way.
- This is unofficial/reverse-engineered access to a public read-only site (no
  auth bypass, no paywalled content) — treat it as scraping-adjacent: don't hammer
  it, and don't rely on it for anything beyond ad hoc reference-model pulls.
