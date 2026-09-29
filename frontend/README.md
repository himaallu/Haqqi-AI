# Haqqi frontend

Next.js (App Router) + Tailwind + shadcn/ui, managed with pnpm.

```sh
pnpm install
pnpm dev        # http://localhost:3000, expects the backend at NEXT_PUBLIC_API_URL
pnpm test       # vitest
pnpm lint && pnpm typecheck
```

shadcn/ui components live in `components/ui/` (config in `components.json`).
