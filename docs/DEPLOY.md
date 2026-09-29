# Deploying Haqqi (free tiers)

Three services, all on free plans (see "0.1 Free stack" in `IMPLEMENTATION_PLAN.md`). Keys and URLs go into
each host's settings, never into the repo.

## 1. Database: Supabase

1. Create a free project at supabase.com.
2. SQL editor → run `create extension if not exists vector;`
3. Click **Connect** (top of the dashboard) → copy the **Session pooler** URI. This is `DATABASE_URL`:
   `postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres`
   - Do **not** use the "Direct connection" host `db.<project-ref>.supabase.co`: on the free plan it is IPv6-only,
     and most hosts (including Hugging Face) can't reach it.
   - Replace `[YOUR-PASSWORD]` including the square brackets.
   - Special characters in the password must be URL-encoded: `@` → `%40`, `#` → `%23`, `/` → `%2F`, `:` → `%3A`.
     Simplest: reset the password to letters and digits only.

Free projects pause after about a week without traffic; open the dashboard to wake one up.

## 2. Backend: Hugging Face Space (Gradio SDK, free)

Docker Spaces are paid, so we use a free **Gradio** Space. It installs `backend/requirements.txt` and runs
`backend/app.py`, which serves our FastAPI app on port 7860; Gradio itself isn't used.

1. Create a new Space: SDK **Gradio**, template **Blank**, hardware **CPU basic (free)**, visibility **Public**.
   The browser has to reach the API, so the Space must be public. The code is already public, and secrets
   stay private in the Space settings.
2. Space settings → **Variables and secrets** → add secrets:
   `DATABASE_URL`, `K2_API_KEY`, `GROQ_API_KEY`, and the variable
   `CORS_ORIGINS=["https://<your-vercel-app>.vercel.app"]`.
3. Create a Hugging Face access token (profile → Settings → Access Tokens → **Write** role).
4. Push the `backend/` folder as the Space's root. Its `README.md` header sets the SDK, Python version and entry
   point. When git asks for a password, use the access token.

   ```sh
   git remote add hf https://huggingface.co/spaces/<user>/<space>
   git subtree push --prefix backend hf main
   ```

   The first push replaces the Space's generated files, which may need `git push --force`:
   `git push hf "$(git subtree split --prefix backend)":main --force`.

   Sprint 8 replaces this with a GitHub Action that deploys on merge to `main`.
5. Check: `curl https://<user>-<space>.hf.space/healthz` → `{"status":"ok","db":"ok",...}`.

Free Spaces sleep after a period without traffic; the first request after that takes a while to wake it.

## 3. Frontend: Vercel

1. Import the GitHub repo in Vercel; set **Root Directory** to `frontend` (Vercel detects Next.js and pnpm).
2. Environment variable: `NEXT_PUBLIC_API_URL=https://<user>-<space>.hf.space`.
3. Deploy. Check: the Vercel URL shows `backend: ok · db: ok`.

Every pull request gets its own preview URL. Add the preview domain to `CORS_ORIGINS` if you want previews
to reach the backend.

## LLM keys

Never paste keys or passwords into a chat, issue or commit. Put them in the host's secret settings, in a local
`.env` (git-ignored), or in the Claude Code cloud environment's environment variables. If a key is exposed,
revoke it and create a new one.

`uv run python -m haqqi.llm.smoke` (from `backend/`, with keys in `.env`) makes one call to K2 and one to
Groq and prints latency and rate-limit headers. It never prints the keys.
