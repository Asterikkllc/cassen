# This is NOT the Next.js you know

This version (16.2.4) has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

# This is NOT the React you know

This version (19.2.4) introduces the React Compiler and changes around `cache`, `use`, async server components, and form actions. When in doubt, check `node_modules/react/dist/docs/` or `node_modules/next/dist/docs/` for current patterns.

# Stack guardrails

- **Auth**: Clerk only. Don't introduce Auth0/Supabase Auth/etc.
- **DB**: Supabase Postgres (with RLS) + Storage. pgvector when needed.
- **Styling**: Tailwind v4 + shadcn/ui on top of `@base-ui/react` primitives (NOT Radix).
- **3D (Workshop)**: WebGPU PBR via three.js / R3F for interactive; Omniverse for ray-traced hero shots. Don't build a custom WebGL renderer.
- **Physics (Test Room)**: Modal-hosted Newton 1.0 + MuJoCo Warp. Never run heavy physics client-side.
- **Unified Runtime**: one control-protocol schema per project drives sim + companion PWA + gamepad/keyboard + firmware. Don't generate any of them in isolation.

PRD lives at `../docs/PRD.md`. Treat it as authoritative when scoping new work.
