---
title: "Cloudflare Workers: Build and Deploy APIs at No Cost"
description: "Learn how to create, test, and launch serverless APIs with Cloudflare Workers—free tier, step‑by‑step guide, trade‑offs, and comparison to other platforms."
date: 2026-10-16
tags:
  - cloudflare
  - serverless
  - api-development
  - free-tools
layout: post
---

## Direct Value Proposition
If you need an API that runs worldwide, scales automatically, and costs nothing for typical hobby or prototype traffic, Cloudflare Workers lets you write JavaScript (or other supported languages) and deploy it in seconds—no servers, no DevOps, no upfront fees.

## What Are Cloudflare Workers?
Cloudflare Workers is a **serverless compute platform** that runs code at the edge of Cloudflare’s global network. "Edge" means the code executes in data centers close to the end‑user, reducing latency. Workers are written in JavaScript, TypeScript, Rust, C, or Go, and are packaged as lightweight scripts (often under 1 MB). The platform isolates each request in a sandbox, so you cannot affect other users.

## Why Choose Workers for APIs?
* **Global latency reduction** – Requests are handled in the nearest Cloudflare POP (point of presence), often under 20 ms.
* **Automatic scaling** – No capacity planning; Cloudflare adds capacity instantly as traffic spikes.
* **Generous free tier** – The free plan covers many low‑to‑moderate workloads, making it ideal for prototypes, student projects, or side‑hustles.
* **Built‑in security** – Workers run in a restricted environment, limiting exposure to OS‑level attacks.
* **Easy integration** – You can attach a Worker directly to a domain, subdomain, or route pattern without configuring a separate load balancer.

## Step‑by‑Step: Building a Simple JSON API
Below is a concrete workflow that takes you from zero to a live API that returns a random joke.

1. **Create a Cloudflare account** – Sign up at the official Cloudflare site ([https://cloudflare.com](https://cloudflare.com)). The free tier is sufficient for this tutorial.
2. **Install Wrangler** – Wrangler is Cloudflare’s CLI tool.
   ```bash
   npm install -g @cloudflare/wrangler
   ```
3. **Generate a new project** – Run the template command.
   ```bash
   wrangler generate joke-api
   cd joke-api
   ```
4. **Write the handler** – Edit `src/index.js`:
   ```javascript
   export default {
     async fetch(request) {
       const jokes = [
         "Why do programmers hate nature? It has too many bugs.",
         "I told my computer I needed a break, and it said \"No problem, I'll go to sleep.\"",
         "Why did the API cross the road? To get to the other endpoint."
       ];
       const random = jokes[Math.floor(Math.random() * jokes.length)];
       return new Response(JSON.stringify({ joke: random }), {
         headers: { "content-type": "application/json" },
       });
     },
   };
   ```
5. **Configure `wrangler.toml`** – Set the route where the API will live.
   ```toml
   name = "joke-api"
   main = "src/index.js"
   compatibility_date = "2024-01-01"
   # Replace with your domain.
   routes = [{ pattern = "myapp.com/api/joke", script = "joke-api" }]
   ```
6. **Publish** – Deploy with a single command.
   ```bash
   wrangler publish
   ```
7. **Test** – Open `https://myapp.com/api/joke` in a browser or curl.
   ```bash
   curl https://myapp.com/api/joke
   ```
   You should see a JSON object with a random joke.

## Managing Environment Variables and Secrets
Sensitive data such as API keys should never be hard‑coded. Wrangler lets you store **secrets** that are injected at runtime.

```bash
wrangler secret put OPENAI_API_KEY
```
After entering the value, you can read it in your Worker with `env.OPENAI_API_KEY`. The secret is encrypted at rest and never exposed to the client.

**Best practice** – Keep the secret name short, and avoid logging its value. If you need multiple keys, store them as separate secrets rather than a JSON blob; this makes rotation easier.

## Performance, Scaling, and Cost Considerations
| Aspect | Free Tier | Paid Tier |
|--------|-----------|----------|
| Request limit | Sufficient for small projects; typical free allowance covers many thousands of daily calls. | Higher limits and dedicated CPU‑time for heavy workloads. |
| CPU time per request | Up to 50 ms of CPU per request (subject to change). | Up to 30 ms per request on the paid plan, with the ability to purchase additional CPU‑time. |
| Custom domains | Supported via Cloudflare DNS. | Same, plus optional dedicated SSL certificates. |
| Analytics | Basic request counts in the dashboard. | Detailed logs, latency breakdowns, and custom metrics. |

**Trade‑offs**
* **Latency vs. Cold Starts** – Workers are instantiated on demand. For the free tier, the first request after a period of inactivity may experience a slight delay (often <100 ms). Paid plans can reduce this by keeping instances warm.
* **CPU limits** – Complex calculations may exceed the free CPU budget, causing the request to be aborted with a `500` error. Break heavy work into smaller chunks or move it to a background queue (e.g., Cloudflare Queues).
* **Data storage** – Workers KV (key‑value store) is free up to a modest quota, but reads have eventual consistency. For strong consistency, consider Durable Objects, which are free for low‑volume use but become billed beyond a threshold.

## Debugging, Testing, and Failure Modes
### Local Development
Wrangler provides a `wrangler dev` command that runs a local server mimicking the edge runtime. Use it to iterate quickly.
```bash
wrangler dev
```
### Common Failure Modes
| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `500 Internal Server Error` with no logs | Exceeded CPU time or unhandled exception | Add `try/catch`, simplify logic, or move heavy work to a queue. |
| `404 Not Found` on route | Route pattern mismatch in `wrangler.toml` | Verify the `routes` array matches the requested URL exactly. |
| `403 Forbidden` when reading a secret | Secret not defined or wrong name | Run `wrangler secret list` and ensure you reference the correct variable. |
| Slow response (>200 ms) | Cold start or network latency to origin | Warm the worker by sending periodic requests, or use a paid plan for reduced cold‑start time. |
### Logging
Use `console.log` inside your Worker; logs appear in the Cloudflare dashboard under **Workers → Logs**. For production debugging, send structured logs to an external service via HTTP, but be mindful of added latency.

## Comparison with Other Serverless Platforms
When deciding whether Workers is the right tool, compare it against popular alternatives.

| Feature | Cloudflare Workers | AWS Lambda@Edge | Vercel Serverless Functions |
|---------|-------------------|----------------|-----------------------------|
| Global edge execution | ✅ (200+ POPs) | ✅ (AWS edge locations) | ❌ (runs in regional zones) |
| Free tier generosity | High – covers many hobby projects | Limited – free tier only for Lambda, not edge |
| Language support | JS/TS, Rust, C, Go | JS/TS (Node.js) | JS/TS, Go, Python (via adapters) |
| Cold‑start latency | Low (sub‑100 ms) | Higher (often >200 ms) | Moderate |
| Built‑in KV store | ✅ Workers KV (eventual consistency) | ❌ Requires DynamoDB | ✅ Vercel KV (beta) |
| Pricing model | Pay‑as‑you‑go after free tier | Pay per request + data transfer | Pay per execution, generous free tier |

**Takeaway** – If you need true edge proximity and a free tier that lets you ship an API without any cost, Workers is hard to beat. If you already rely on AWS services and need tight integration with other AWS resources, Lambda@Edge may make sense despite higher latency.

## Sources
- [Cloudflare Workers documentation](https://developers.cloudflare.com/workers/)
- [Cloudflare Workers pricing page](https://www.cloudflare.com/products/workers/)
- [Google Search Central blog](https://developers.google.com/search/blog)

## Evidence‑Based Takeaway and Next Workflow Step
Cloudflare Workers provides a frictionless path to launch globally distributed APIs without upfront expense. By following the step‑by‑step workflow above, you can have a functional endpoint in minutes, keep secrets safe, and monitor performance from the dashboard. The next logical step is to add persistence—store user submissions in Workers KV or Durable Objects—and expand the API with versioned routes. This incremental approach lets you stay within the free tier while gaining real‑world feedback before scaling.
