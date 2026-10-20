---
title: "Cloudflare Workers: Build and Deploy APIs at No Cost"
description: "Create, test, and ship a serverless API on Cloudflare Workers' free plan: current Wrangler commands, verified limits, trade-offs, and when to use something else."
date: 2026-10-16
last_modified_at: 2026-10-19
tags:
  - cloudflare
  - serverless
  - api-development
  - free-tools
layout: post
---

> **Updated October 19, 2026:** corrected plan limits, replaced retired Wrangler commands, and fixed the route configuration. All limits were checked against Cloudflare's documentation on this date.

## The short version

Cloudflare Workers runs your code in Cloudflare's data centers worldwide, scales automatically, and is free up to **100,000 requests per day**. For prototypes, internal tools, webhooks, and side projects, you can ship a production API without paying for a server.

## What Workers are

Workers is a serverless platform built on V8 isolates (the same engine as Chrome) rather than containers. Each request runs in a lightweight sandbox close to the user. Supported languages: JavaScript and TypeScript natively, Python (beta), and Rust/C/C++/Go via WebAssembly.

Because isolates start in milliseconds, Workers has no meaningful cold-start problem — and there is no paid "keep-warm" tier, because there's nothing to keep warm.

## Free plan limits (verify before you build)

| Limit | Free | Paid ($5/mo minimum) |
|---|---|---|
| Requests | 100,000/day (resets 00:00 UTC), 1,000/min burst | 10M/month included, then $0.30/M |
| CPU time per request | **10 ms** | 30 s default, up to 5 min |
| Subrequests (`fetch` calls) per request | 50 | 1,000 |
| Durable Objects | SQLite-backed only, with daily limits | SQLite or KV-backed |

Key point: **CPU time is not wall time.** Time spent waiting on `fetch()`, KV, or a database doesn't count. A Worker that calls an LLM API for 8 seconds may use under 5 ms of CPU. Most Workers use 1–2 ms.

Source: [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), [Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/).

## Build a JSON API in five steps

### 1. Create the project

```bash
npm create cloudflare@latest joke-api
cd joke-api
```

Choose the "Hello World" Worker template. This installs Wrangler (Cloudflare's CLI) as a local dev dependency — no global install needed.

> Old tutorials use `npm install -g @cloudflare/wrangler`, `wrangler generate`, and `wrangler publish`. All three are retired. Use `npm create cloudflare` and `wrangler deploy`.

### 2. Write the handler

`src/index.js`:

```js
const JOKES = [
  "Why do programmers hate nature? It has too many bugs.",
  "I told my computer I needed a break. It said: no problem, I'll go to sleep.",
  "Why did the API cross the road? To get to the other endpoint.",
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (url.pathname !== "/api/joke") {
      return Response.json({ error: "not_found" }, { status: 404 });
    }
    if (request.method !== "GET") {
      return Response.json({ error: "method_not_allowed" }, { status: 405 });
    }

    const joke = JOKES[Math.floor(Math.random() * JOKES.length)];
    return Response.json({ joke }, {
      headers: { "cache-control": "no-store" },
    });
  },
};
```

### 3. Configure

`wrangler.toml`:

```toml
name = "joke-api"
main = "src/index.js"
compatibility_date = "2026-10-01"

[observability]
enabled = true

# Optional: serve on your own domain (domain must be on Cloudflare DNS).
# Without this, you get https://joke-api.<your-subdomain>.workers.dev
# routes = [{ pattern = "myapp.com/api/*", zone_name = "myapp.com" }]
```

Note the trailing `*` in the route pattern and the `zone_name` key — a pattern without a wildcard only matches that exact path.

### 4. Run locally, then deploy

```bash
npx wrangler dev      # local server at http://localhost:8787
npx wrangler deploy   # live in seconds
```

### 5. Test

```bash
curl https://joke-api.<your-subdomain>.workers.dev/api/joke
```

## Secrets

Never hard-code keys.

```bash
npx wrangler secret put OPENAI_API_KEY
```

Read it as `env.OPENAI_API_KEY`. Secrets are encrypted and never exposed to clients. For local dev, put values in a `.dev.vars` file and add it to `.gitignore`.

Store each key as its own secret rather than one JSON blob — rotation is cleaner.

## Storage options

| Need | Use | Notes |
|---|---|---|
| Config, cache, read-heavy lookups | **Workers KV** | Eventually consistent; writes can take up to ~60 s to propagate globally |
| Relational data | **D1** | Managed SQLite, free tier available |
| Strong consistency, counters, rate limits, WebSockets | **Durable Objects** | SQLite-backed DOs are available on the free plan |
| Files, images, backups | **R2** | S3-compatible, no egress fees |
| Background or heavy work | **Queues** / **Cron Triggers** | Move anything CPU-heavy off the request path |

## Debugging

| Symptom | Likely cause | Fix |
|---|---|---|
| Error 1102 "Worker exceeded resource limits" | Over the CPU limit (10 ms on free) | Reduce CPU work, move it to a Queue, or upgrade |
| Route returns origin page or 404 | Route pattern missing `/*` or wrong `zone_name` | Fix the pattern; confirm the domain is proxied through Cloudflare |
| `env.MY_SECRET` is `undefined` | Secret not set, misspelled, or missing from `.dev.vars` locally | `npx wrangler secret list` |
| Uncaught exception → 500 | Unhandled error | Wrap logic in `try/catch` and return a JSON error |

**Logs:** run `npx wrangler tail` for live logs, or use Workers Logs in the dashboard (enabled by the `[observability]` block above). Never log secret values.

## Workers vs. alternatives

| | Cloudflare Workers | AWS Lambda@Edge | Vercel Functions |
|---|---|---|---|
| Runs at the edge by default | Yes | Yes (CloudFront locations) | Regional by default |
| Free tier | 100K req/day | No Lambda@Edge free tier | Hobby plan, non-commercial use |
| Runtime model | V8 isolates | Containers | Containers (Fluid compute) |
| Cold starts | Negligible | Noticeable | Reduced but present |
| Languages | JS/TS, Python (beta), Wasm | Node.js, Python | Node.js, Python, Go, Ruby |
| Built-in storage | KV, D1, R2, Durable Objects | Bring your own (DynamoDB, S3) | Marketplace integrations |

**Pick Workers** when you want global low latency and a real free tier. **Pick Lambda** when you're already deep in AWS. **Pick Vercel** when the API lives alongside a Next.js frontend you already host there.

Workers' main constraint is not Node.js: many Node APIs work with the `nodejs_compat` flag, but native modules and long CPU-bound jobs don't belong here.

## Next step

Add persistence: store submissions in D1 (relational) or a Durable Object (strongly consistent), then version your routes (`/api/v1/...`). Both fit inside the free plan while you collect real usage data.

## Sources

- [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/)
- [Cloudflare Workers pricing](https://developers.cloudflare.com/workers/platform/pricing/)
- [Durable Objects](https://developers.cloudflare.com/durable-objects/)
- [Wrangler commands](https://developers.cloudflare.com/workers/wrangler/commands/)
