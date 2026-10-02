# Deploying Haqqi (free tiers)

Three services, all on free plans (see "0.1 Free stack" in `IMPLEMENTATION_PLAN.md`). Keys and URLs go into
each host's settings, never into the repo.

## 1. Database: Supabase

1. Create a free project at supabase.com.
2. SQL editor → run `create extension if not exists vector;`
3. Click **Connect** (top of the dashboard) → copy the **Session pooler** URI. This is `DATABASE_URL`:
   `postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres`
   - Do **not** use the "Direct connection" host `db.<project-ref>.supabase.co`: on the free plan it is IPv6-only,
     and most hosts (including Render) can't reach it.
   - Replace `[YOUR-PASSWORD]` including the square brackets.
   - Special characters in the password must be URL-encoded: `@` → `%40`, `#` → `%23`, `/` → `%2F`, `:` → `%3A`.
     Simplest: reset the password to letters and digits only.

Free projects pause after about a week without traffic; open the dashboard to wake one up.

## 2. Backend: Render (free web service)

Render builds `backend/Dockerfile` straight from GitHub. The service is described in `render.yaml` at the repo
root, so there is nothing to push by hand: every commit touching `backend/` redeploys.

1. Sign up at render.com with **GitHub** and allow access to the `Haqqi-AI` repository.
2. **New → Blueprint** → pick `himaallu/Haqqi-AI`. Render reads `render.yaml` and shows one web service,
   `haqqi-api` (free plan, Frankfurt).
3. Fill in the three secrets it asks for: `DATABASE_URL` (the Supabase Session pooler URI from step 1),
   `K2_API_KEY`, `GROQ_API_KEY`. `CORS_ORIGINS` is already set in `render.yaml`.
4. **Apply**. The first build takes a few minutes; watch it under the service's **Logs**.
5. Check: `curl https://haqqi-api.onrender.com/healthz` → `{"status":"ok","db":"ok",...}`.
   Your exact URL is shown at the top of the service page. If the name was taken, it has a suffix.

Free services sleep after about 15 minutes without traffic; the first request after that takes about a minute.
The free plan has 512 MB of RAM (see flag 15 in the plan for what that means for embeddings).
`render.yaml` deploys the `main` branch: merging a pull request redeploys the backend.

## 3. Frontend: Vercel

1. Import the GitHub repo in Vercel; set **Root Directory** to `frontend` (Vercel detects Next.js and pnpm).
2. Environment variable: `NEXT_PUBLIC_API_URL=https://haqqi-api.onrender.com` (your Render URL).
   Vercel bakes it in at build time, so redeploy after changing it.
3. Deploy. Check: the Vercel URL shows `backend: ok · db: ok`.

Every pull request gets its own preview URL. Add the preview domain to `CORS_ORIGINS` in `render.yaml` if you
want previews to reach the backend.

## LLM keys

Never paste keys or passwords into a chat, issue or commit. Put them in the host's secret settings, in a local
`.env` (git-ignored), or in the Claude Code cloud environment's environment variables. If a key is exposed,
revoke it and create a new one.

`uv run python -m haqqi.llm.smoke` (from `backend/`, with keys in `.env`) makes one call to K2 and one to
Groq and prints latency and rate-limit headers. It never prints the keys.
