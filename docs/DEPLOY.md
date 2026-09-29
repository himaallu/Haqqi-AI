# Deploying Haqqi (free tiers)

Three services, all on free plans (see "0.1 Free stack" in `IMPLEMENTATION_PLAN.md`). Keys and URLs go into
each host's settings, never into the repo.

## 1. Database: Supabase

1. Create a free project at supabase.com.
2. SQL editor → run `create extension if not exists vector;`
3. Project settings → Database → copy the **connection pooler** URI (port 6543). This is `DATABASE_URL`.

Free projects pause after about a week without traffic; open the dashboard to wake one up.

## 2. Backend: Hugging Face Spaces (Docker)

1. Create a new Space: SDK **Docker**, hardware **CPU basic (free)**, visibility **public**.
   The browser has to reach the API, so the Space must be public. The code is already public, and secrets
   stay private in the Space settings.
2. Space settings → **Variables and secrets** → add secrets:
   `DATABASE_URL`, `K2_API_KEY`, `GROQ_API_KEY`, and the variable
   `CORS_ORIGINS=["https://<your-vercel-app>.vercel.app"]`.
3. Push the `backend/` folder as the Space's root (its `README.md` header tells Spaces to build the Dockerfile):

   ```sh
   git remote add hf https://huggingface.co/spaces/<user>/<space>
   git subtree push --prefix backend hf main
   ```

   Sprint 8 replaces this with a GitHub Action that deploys on merge to `main`.
4. Check: `curl https://<user>-<space>.hf.space/healthz` → `{"status":"ok","db":"ok",...}`.

Free Spaces sleep after a period without traffic; the first request after that takes a while to wake it.

## 3. Frontend: Vercel

1. Import the GitHub repo in Vercel; set **Root Directory** to `frontend` (Vercel detects Next.js and pnpm).
2. Environment variable: `NEXT_PUBLIC_API_URL=https://<user>-<space>.hf.space`.
3. Deploy. Check: the Vercel URL shows `backend: ok · db: ok`.

Every pull request gets its own preview URL. Add the preview domain to `CORS_ORIGINS` if you want previews
to reach the backend.

## LLM keys

`uv run python -m haqqi.llm.smoke` (from `backend/`, with keys in `.env`) makes one call to K2 and one to
Groq and prints latency and rate-limit headers. It never prints the keys.
