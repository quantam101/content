---
title: "How to Set Up a Free Postgres Database on Supabase – Step‑by‑Step Guide"
description: "Learn how to create, configure, and connect a free PostgreSQL database on Supabase in minutes. Includes setup steps, troubleshooting tips, and free‑vs‑paid feature comparison."
date: 2026-10-13
tags:
  - Supabase
  - PostgreSQL
  - Free Database
  - Backend
layout: post
---

## Quick answer: you can have a fully functional PostgreSQL database up and running on Supabase in under ten minutes, and you won’t pay a cent as long as you stay within the free tier limits.

Supabase is an open‑source backend‑as‑a‑service platform that bundles PostgreSQL, authentication, storage, and real‑time APIs. The free tier gives you a managed Postgres instance, a web console, and API access without requiring a credit card. Below is a complete, evidence‑backed workflow that walks you through account creation, project setup, connection configuration, and common failure modes.

---

## 1. Why choose Supabase’s free Postgres?

- **Fully managed** – Supabase runs the database on cloud infrastructure, handles backups, and applies security patches automatically.
- **Zero‑cost entry point** – The free tier includes 500 MB of database storage, 2 GB of file storage, and generous API request limits, which is sufficient for learning, prototypes, or low‑traffic apps.
- **Built‑in tooling** – A web‑based dashboard, SQL editor, and REST/GraphQL APIs are ready out of the box, so you can start querying without installing extra software.
- **Open‑source compatibility** – Because Supabase uses vanilla PostgreSQL, anything you learn transfers to self‑hosted or cloud‑hosted Postgres instances.

> **Evidence note:** The feature list and limits are documented in the official Supabase pricing page as of 2024, and the PostgreSQL core behavior is defined by the PostgreSQL Global Development Group.

---

## 2. Create a Supabase account and a new project

### 2.1 Sign up
1. Visit **https://supabase.com** and click *Sign up*.
2. Choose an email/password or use a GitHub OAuth flow. No credit‑card is required for the free tier.
3. Verify your email address – Supabase sends a short confirmation link.

### 2.2 Start a new project
1. After logging in, click **New project** on the dashboard.
2. Fill in the required fields:
   - **Project name** – a human‑readable identifier (e.g., *my‑first‑db*).
   - **Database password** – a strong password; Supabase will store it securely.
   - **Region** – pick a location close to your users for lower latency (e.g., *us-east-1*).
3. Click **Create project**. Supabase provisions a PostgreSQL instance, which typically takes 30‑60 seconds.

You will be redirected to the project overview page where the **Database** tab displays the connection details.

---

## 3. Configure the Postgres database

### 3.1 Locate the connection string
In the **Settings → Database** section you’ll find a URI that looks like:
```
postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres
```
Replace `YOUR_PASSWORD` with the password you set earlier. This string is what client tools use to connect.

### 3.2 Set up role‑based access (optional but recommended)
Supabase creates a default `postgres` superuser, but for production‑like safety you should:
1. Open the SQL editor from the dashboard.
2. Run:
```sql
CREATE ROLE app_user WITH LOGIN PASSWORD 'StrongPass123!';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;
```
This creates a limited user (`app_user`) that can be used by your application, reducing the risk of accidental schema changes.

### 3.3 Enable extensions you may need
PostgreSQL supports extensions like `pgcrypto` for encryption or `uuid-ossp` for UUID generation. To enable:
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```
Extensions are free on the Supabase tier, but some heavy‑weight extensions may be restricted in the free plan.

---

## 4. Connect from local tools

### 4.1 Using `psql`
If you have the PostgreSQL command‑line client installed, run:
```
psql "postgresql://app_user:StrongPass123!@db.YOUR_PROJECT_ID.supabase.co:5432/postgres"
```
You should see the `psql` prompt (`postgres=#`). Try a simple query:
```sql
SELECT version();
```
If you get a version string, the connection works.

### 4.2 Using a GUI client (e.g., DBeaver, TablePlus)
1. Open the client and create a new PostgreSQL connection.
2. Paste the connection URI or fill the fields manually (host, port, database, user, password).
3. Test the connection – most GUIs show a green check if successful.

### 4.3 Connecting from code (Node.js example)
```js
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://YOUR_PROJECT_ID.supabase.co';
const supabaseKey = 'anon-public-key-from-Settings→API'; // public anon key

const supabase = createClient(supabaseUrl, supabaseKey);

// Example: fetch rows from a table called "todos"
const { data, error } = await supabase.from('todos').select('*');
console.log(data, error);
```
The `@supabase/supabase-js` library talks to the Postgres instance via automatically generated REST endpoints, so you never need the raw connection string in front‑end code.

---

## 5. Common pitfalls and how to troubleshoot

| Symptom | Likely cause | Quick fix |
|---------|--------------|-----------|
| **Connection timed out** | Wrong host or region firewall | Verify the host part of the URI matches the one shown in the dashboard. Ensure your IP is not blocked by Supabase’s security settings (Settings → Network). |
| **Authentication failed** | Incorrect password or role | Double‑check the password you entered. Remember that the default `postgres` user is a superuser; if you created `app_user`, use that name. |
| **“permission denied for schema public”** | Role lacks privileges | Run the `GRANT` statements shown in section 3.2, or connect as the `postgres` superuser to adjust permissions. |
| **Database size limit reached** | Exceeded 500 MB free storage | Clean up unused tables or rows. Supabase offers a **Database → Settings → Reset** button for a fresh start, or consider upgrading to a paid tier if you need more space. |
| **Extensions not found** | Extension not enabled on free tier | Check Supabase’s documentation for the list of supported extensions on the free plan. If an extension is unavailable, you may need to self‑host PostgreSQL. |

When you encounter an error, the Supabase dashboard logs (Settings → Logs) often contain the exact PostgreSQL error message, which you can copy into a search engine or the official PostgreSQL docs for deeper insight.

---

## 6. Free tier vs. paid features – quick comparison

| Feature | Free tier (as of 2024) | Paid tier (Pro) |
|---------|------------------------|-----------------|
| Database storage | 500 MB | Up to 8 GB per project (higher plans allow more) |
| Daily API request limit | 2 M (combined across auth, storage, edge functions) | 10 M+ (scales with plan) |
| Backups | Automatic daily backup, retained 7 days | Point‑in‑time recovery, up to 30 days retention |
| Row‑level security (RLS) | Fully supported | Fully supported |
| Custom domain for API | Not available | Available on Pro and higher |
| Dedicated support | Community Discord, docs | Email/SLA support |
| Edge functions runtime | Limited to 125 ms per request | Up to 1 s and higher concurrency |

The free tier is generous for learning, personal projects, and small MVPs. When you outgrow storage or need tighter SLAs, the Pro plan unlocks higher limits and dedicated support.

---

## 7. Best practices and next workflow step

1. **Version control your schema** – Use Supabase’s `supabase db dump` command to export the schema to a SQL file and store it in Git. This makes rollbacks and team collaboration easy.
2. **Enable Row‑Level Security (RLS)** – Even in a prototype, defining policies early prevents accidental data leaks.
3. **Monitor usage** – The dashboard shows real‑time metrics for storage, API calls, and CPU. Set alerts if you approach the free limits.
4. **Automate migrations** – Tools like `dbmate` or `Flyway` work with Supabase because it’s standard PostgreSQL.
5. **Plan for growth** – If you anticipate exceeding the 500 MB limit, design your tables with partitioning or consider archiving old rows to Supabase Storage.

**Takeaway:** You can spin up a production‑grade PostgreSQL database on Supabase without spending a penny, provided you respect the free‑tier quotas and follow basic security hygiene. The next logical step is to script your schema migrations and integrate the Supabase client into your application code, turning the database from a sandbox into the backbone of your product.

## Sources
- Supabase Pricing & Limits – https://supabase.com/pricing
- Supabase Documentation – Database section – https://supabase.com/docs/guides/database
- PostgreSQL Official Documentation – https://www.postgresql.org/docs/current/index.html

