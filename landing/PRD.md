# Landing Page Build — Phase-by-Phase PRD for Claude Code

**Project:** Pre-launch landing page for Cassen
**Domain:** cassen.ai
**Build tool:** Claude Code
**Target stack:** Next.js 15 + Tailwind v4 + shadcn/ui + Magic UI + Motion + Supabase + Resend + Vercel
**Estimated build time:** 5–10 days, working in focused sessions

---

## How to Use This Document

This document breaks the landing page into 13 sequential phases. Each phase delivers exactly one function. Each phase is self-contained — you can paste it into Claude Code as its own prompt and verify the result before moving on.

**Workflow per phase:**
1. Open Claude Code in the project directory.
2. Copy the entire phase block (from `## PHASE N` to the next `## PHASE`).
3. Paste it as your prompt.
4. Let Claude Code execute the steps.
5. Run the acceptance test at the end of the phase.
6. Only move to the next phase when the current one passes.

**MVP cutoff:** Phases 1–5 give you a live, functional landing page that captures emails and sends welcome emails. After Phase 5 you have something shippable. Phases 6–13 are layered enhancements.

**Placeholders to replace before starting:**
- `[YOUR EMAIL]` — your contact email (e.g., hello@cassen.ai once domain is live)
- `[YOUR NAME]` — your full name for the welcome email signature
- `[ADMIN EMAIL]` — the email you'll use to access the admin dashboard
- `[HEADLINE]` — pick one from the options in Phase 2
- `[SUBHEADLINE]` — pick one from the options in Phase 2

Cassen is the locked product name. Domain is cassen.ai.

---

## PHASE 1 — Project Initialization & Deploy a Live URL

### Goal
Set up the Next.js project, deploy a placeholder page to Vercel, and confirm a live URL is reachable.

### What this phase delivers
A live URL on Vercel showing a "Coming soon" placeholder. No styling yet, no signup yet — just a page on the internet.

### Dependencies
- A GitHub account
- A Vercel account (free) connected to your GitHub
- Node.js 20+ installed locally
- A purchased domain (optional for this phase, can add later)

### Tech & files
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS v4
- ESLint
- Files created: standard Next.js scaffold, modified `app/page.tsx`

### Implementation steps for Claude Code
```
1. Initialize a new Next.js 15 project in the current directory using:
   npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

2. Replace the contents of src/app/page.tsx with a minimal placeholder:
   - A centered, dark-background page
   - A single line of text: "Cassen — coming soon"
   - No styling beyond Tailwind defaults

3. Modify src/app/layout.tsx to set:
   - title: "Cassen"
   - description: "Describe a product. Get a manufacturable design back."
   - dark background by default (bg-neutral-950 on body)

4. Initialize a git repository, commit, and push to a new GitHub repo named cassen-landing.

5. Provide instructions for connecting the GitHub repo to Vercel and deploying.
```

### Acceptance criteria
- Local dev server runs at `http://localhost:3000` and shows the placeholder.
- A live Vercel URL exists (something like `cassen-landing.vercel.app`) and shows the same placeholder.
- The page loads in under 1 second.

### Test
Open the Vercel URL in an incognito window. The placeholder text should be visible. Done.

---

## PHASE 2 — Hero Section (Visual Only, No Form Logic)

### Goal
Build the above-the-fold hero with the headline, subheadline, and visual structure for the email form. The form will be wired up in Phase 3.

### What this phase delivers
A polished hero section that tells the visitor what the product is, who it's for, and gives them a place to enter their email. The form input shows but doesn't yet save anywhere.

### Dependencies
- Phase 1 complete

### Pick before starting
**Headline (pick one and use it consistently):**
- Option A: *"Describe a product. Get a manufacturable design back."*
- Option B: *"The AI engineer for physical products."*
- Option C: *"Hardware design at the speed of conversation."*
- Option D: *"From prompt to PCB. From idea to enclosure."*

**Subheadline (pick one):**
- Option A: *"For founders, makers, and product teams. Skip months of CAD work — get DFM-ready designs, BOMs, and renders from a sentence."*
- Option B: *"An AI agent that researches, designs, and prepares your hardware for manufacturing — all from plain language."*

### Tech & files
- shadcn/ui for the button and input components
- Magic UI for the animated gradient background
- Motion (formerly Framer Motion) for fade-in animations
- Files created/modified: `src/components/hero.tsx`, `src/components/ui/*`, updates to `src/app/page.tsx` and `src/app/globals.css`

### Implementation steps for Claude Code
```
1. Install shadcn/ui:
   npx shadcn@latest init
   - Choose: Default, New York style, Neutral base, CSS variables yes

2. Install required shadcn components:
   npx shadcn@latest add button input

3. Install Motion and Magic UI:
   npm install motion
   Follow Magic UI install at https://magicui.design/docs/installation
   Then add the AnimatedGradientText and DotPattern components from Magic UI.

4. Create src/components/hero.tsx with this structure:
   - Full-screen height (min-h-screen) section
   - Dark background (bg-neutral-950)
   - Subtle dot-pattern or gradient overlay from Magic UI
   - Centered content vertically and horizontally:
     a. Small pill/badge at top: "Pre-launch • Joining a private beta"
     b. Large headline: [HEADLINE] — text-5xl on mobile, text-7xl on desktop, font-bold, tracking-tight, white text
     c. Subheadline: [SUBHEADLINE] — text-lg on mobile, text-xl on desktop, text-neutral-400, max-w-2xl
     d. Email form row: email input + "Get early access" button, side by side on desktop, stacked on mobile
     e. Micro trust line below form: "No spam. Just one email when access opens."
   - Use Motion to fade in each element with staggered delays (badge → headline → subheadline → form)
   - Form is non-functional in this phase — the button can console.log the email but does nothing else.

5. Update src/app/page.tsx to import and render <Hero />.

6. Make sure the page is mobile-responsive: full-width form on mobile, side-by-side on md and above.

7. Use Inter or Geist as the font (configure in src/app/layout.tsx).
```

### Acceptance criteria
- Hero section fills the viewport on first load.
- Headline, subheadline, form, and trust line all visible without scrolling on a 1920×1080 screen.
- On mobile (375px wide), all elements stack cleanly with no horizontal scroll.
- Elements fade in with a smooth stagger on first paint.
- Form input accepts text but does not save anywhere yet.
- Lighthouse performance score is 90+.

### Test
1. Open the local URL on desktop. The hero should fill the screen and feel intentional, not empty.
2. Resize to mobile width. The layout should stack and remain readable.
3. Open Chrome DevTools → Lighthouse → run a performance audit. Score should be 90+.

---

## PHASE 3 — Email Signup Function (Database + API + Form Wiring)

### Goal
Make the signup form actually work. Emails entered should be stored in a Supabase database table.

### What this phase delivers
A working email capture. When a user submits the form, the email is saved to a Postgres table in Supabase. Duplicate emails show a friendly message. Invalid emails show a validation error.

### Dependencies
- Phase 2 complete
- A free Supabase account (supabase.com)

### Tech & files
- Supabase project + `waitlist` table
- Server Action in Next.js for the form submission
- Zod for email validation
- Files created/modified: `src/lib/supabase.ts`, `src/app/actions/signup.ts`, `src/components/signup-form.tsx`, `.env.local`

### Implementation steps for Claude Code
```
1. Guide the user to create a new Supabase project at supabase.com.
   - Project name: cassen
   - Database password: (user generates and saves)
   - Region: closest to expected user base

2. In the Supabase SQL editor, run this schema:
   create table waitlist (
     id bigint generated by default as identity primary key,
     email text unique not null,
     referrer text,
     metadata jsonb,
     approved boolean not null default false,
     position bigint generated always as (id) stored,
     created_at timestamptz default now()
   );
   alter table waitlist enable row level security;

   -- Policy: anyone can insert, no one can read (we'll read via service role)
   create policy "anon can insert" on waitlist
     for insert to anon
     with check (true);

3. From Supabase dashboard → Project Settings → API, copy:
   - Project URL
   - anon public key
   - service_role secret key

4. Create .env.local in the project root:
   NEXT_PUBLIC_SUPABASE_URL=...
   NEXT_PUBLIC_SUPABASE_ANON_KEY=...
   SUPABASE_SERVICE_ROLE_KEY=...

   Add .env.local to .gitignore (verify).

5. Install dependencies:
   npm install @supabase/supabase-js zod

6. Create src/lib/supabase.ts:
   - Export a client-safe supabase instance using anon key
   - Export a server-only admin client using service_role key (only import this in server actions)

7. Create src/app/actions/signup.ts as a Server Action:
   - Validate email with Zod (z.string().email())
   - Insert into waitlist table
   - Catch unique-violation (Postgres error code 23505) and return friendly "you're already on the list" message
   - Return { success: true, position: number } on success, with the row's id as position
   - Return { success: false, error: string } on failure

8. Refactor src/components/signup-form.tsx (extracted from hero):
   - Use a client component
   - Use useFormState / useFormStatus from React 19 (or useTransition pattern)
   - Show inline loading state on the button
   - On success, replace the form with a success message that shows the position
   - On error, show error inline below the input
   - Keep the visual style consistent with Phase 2

9. Wire the SignupForm into Hero so it replaces the static form from Phase 2.
```

### Acceptance criteria
- Submitting a valid email saves a row in the Supabase `waitlist` table (verify in Supabase dashboard).
- Submitting the same email twice returns "you're already on the list" without crashing.
- Submitting an invalid email shows a validation error inline.
- Loading state shows during submission.
- Success state shows position number ("You're #1" for the first signup).

### Test
1. Submit your own email through the form.
2. Open the Supabase dashboard → Table Editor → waitlist. You should see the row.
3. Submit the same email again — should show duplicate message.
4. Submit "notanemail" — should show validation error.

---

## PHASE 4 — Welcome Email Automation (Resend Integration)

### Goal
Send an automatic welcome email to every new signup within seconds.

### What this phase delivers
Within 10 seconds of signup, the user receives a styled welcome email confirming their spot, sharing the vision in a few sentences, and asking one question to invite a reply.

### Dependencies
- Phase 3 complete
- A free Resend account (resend.com)
- A domain you own (or use Resend's onboarding domain for testing)

### Tech & files
- Resend SDK
- React Email for templates
- Files created/modified: `src/emails/welcome.tsx`, `src/lib/resend.ts`, update to `src/app/actions/signup.ts`

### Implementation steps for Claude Code
```
1. Guide the user to:
   - Create a Resend account at resend.com
   - Add and verify their domain (or use the testing domain initially)
   - Generate an API key
   - Add to .env.local: RESEND_API_KEY=re_...
   - Add: FROM_EMAIL=[YOUR EMAIL or hello@yourdomain.com]

2. Install dependencies:
   npm install resend react-email @react-email/components

3. Create src/emails/welcome.tsx as a React Email template:
   - Subject (set in send call, not template): "You're in. Welcome to Cassen."
   - Greeting: "Hey,"
   - Paragraph 1: "You just joined the waitlist for Cassen — thank you. You're #{position} in line."
   - Paragraph 2 (the vision in 2 sentences): "We're building an AI agent that turns plain-language descriptions into manufacturable hardware designs. Think CAD, BOMs, firmware, all generated from a sentence."
   - Paragraph 3 (the question that invites a reply): "Quick question while it's fresh — what's the first physical product you'd describe to it? Hit reply and tell me. I read every response."
   - Sign-off: "[YOUR NAME], building Cassen"
   - Footer with unsubscribe placeholder
   - Use clean typography, max-width 600px, light theme (most email clients still default to light)

4. Create src/lib/resend.ts that exports a sendWelcomeEmail(email, position) function.

5. Update src/app/actions/signup.ts:
   - After successful Supabase insert, call sendWelcomeEmail(email, position)
   - Wrap in try/catch — if email fails, do NOT fail the signup. Log the error.
   - Use Promise to not block the response — fire-and-forget pattern with proper error logging.

6. Test locally with the React Email dev server:
   npx react-email dev
```

### Acceptance criteria
- New signup triggers a welcome email within 10 seconds.
- The email renders correctly in Gmail (web), Apple Mail (iOS), and Outlook.
- The "reply" address is your real inbox (replies to the welcome email reach you).
- A failed email send does NOT fail the signup — the row still saves and the user still sees success.

### Test
1. Sign up with a test email you can check.
2. Confirm the email arrives within seconds.
3. Reply to the email — confirm the reply lands in your inbox.
4. Sign up another email and disable Resend temporarily (invalidate the API key in .env.local) — confirm signup still succeeds even though email fails.

---

## PHASE 5 — Post-Signup Confirmation State

### Goal
After successful signup, replace the form with a thoughtful confirmation experience that includes the user's position and primes them to share.

### What this phase delivers
A visually distinct success state that shows the user's waitlist position, a "what happens next" message, and a single share-to-Twitter/X link with pre-written copy.

### Dependencies
- Phase 4 complete

### Tech & files
- Update to `src/components/signup-form.tsx`
- New component `src/components/signup-success.tsx`

### Implementation steps for Claude Code
```
1. Create src/components/signup-success.tsx:
   - Animated checkmark or sparkle icon (use Magic UI's Confetti or shadcn's animated success state)
   - Heading: "You're in."
   - Subheading: "You're #{position} on the waitlist."
   - Body: "We'll email when access opens. Until then, check your inbox — there's already a question for you."
   - One subtle button/link: "Share with someone who builds things"
     - Pre-fills X/Twitter intent URL with text: "Just joined the waitlist for Cassen — describe a product, get a manufacturable design back. cassen.ai"
     - Opens in new tab
   - All elements fade in with motion stagger

2. Update src/components/signup-form.tsx:
   - When the action returns { success: true, position }, render <SignupSuccess position={position} /> in place of the form
   - Keep the transition smooth — fade out form, fade in success state

3. Make sure the success state is responsive on mobile.
```

### Acceptance criteria
- After signup, form is replaced with a clean success state.
- Position number is visible and matches Supabase row id.
- Share button opens X/Twitter compose with the correct prefilled text.
- Transition between form and success feels intentional, not jarring.

### Test
1. Sign up a new email and watch the form transition to success.
2. Confirm position number shows correctly.
3. Click the share button — Twitter/X should open with the prefilled tweet.

---

## ✅ MVP COMPLETE

After Phase 5 you have a live, functional landing page. Stop here if you want to start sharing the URL while building the rest. Below phases are enhancements that increase conversion and credibility.

---

## PHASE 6 — "How It Works" Section

### Goal
Add a 3-step explanation below the hero so visitors who don't immediately sign up can understand the product.

### What this phase delivers
A clean 3-card section explaining the user journey in plain language, with simple iconography or numbers.

### Dependencies
- Phase 5 complete

### Tech & files
- New component `src/components/how-it-works.tsx`
- Lucide React icons (already included with shadcn)

### Implementation steps for Claude Code
```
1. Create src/components/how-it-works.tsx:
   - Section padding: py-24 on desktop, py-16 on mobile
   - Centered section header:
     - Small uppercase eyebrow: "HOW IT WORKS"
     - Headline: "From sentence to shipped product"
     - One-line subhead: "Three steps. No engineering required."
   - Three cards in a grid (1 column mobile, 3 columns desktop):
     Card 1:
       - Number "01" or icon (MessageSquare from Lucide)
       - Title: "Describe what you want to build"
       - Body: "A smart planter, a custom robot, a wearable — anything physical. Plain language, no jargon."
     Card 2:
       - Number "02" or icon (Cpu from Lucide)
       - Title: "Watch the agent design it"
       - Body: "Components researched, parts sourced, design assembled in 3D. Validated in physics simulation before you commit."
     Card 3:
       - Number "03" or icon (Package from Lucide)
       - Title: "Order the parts or the finished product"
       - Body: "Get a complete BOM with one-click ordering, or have the assembled prototype shipped to your door."

2. Use subtle borders (border-neutral-800), dark card backgrounds (bg-neutral-900/50), generous padding inside cards.

3. Add scroll-triggered fade-in with Motion (whileInView).

4. Import and render <HowItWorks /> below <Hero /> in src/app/page.tsx.
```

### Acceptance criteria
- Section appears immediately below the hero.
- Cards stack vertically on mobile, 3-across on desktop.
- Cards fade in as they enter the viewport.
- Visual style matches the hero — same dark theme, same typography.

### Test
Scroll down from the hero. The section should appear naturally and explain the product in under 10 seconds of reading.

---

## PHASE 7 — Use Cases / Examples Grid

### Goal
Show concrete examples of what users can build, anchoring the abstract "AI hardware agent" pitch in real, recognizable products.

### What this phase delivers
A grid of 6 example use cases with short descriptions. Each card represents a category of project the agent can handle.

### Dependencies
- Phase 6 complete

### Tech & files
- New component `src/components/use-cases.tsx`
- Lucide icons

### Implementation steps for Claude Code
```
1. Create src/components/use-cases.tsx:
   - Section header:
     - Eyebrow: "USE CASES"
     - Headline: "Built for everything physical"
     - Subhead: "From hobby projects to commercial products."
   - 6-card grid (1 col mobile, 2 col tablet, 3 col desktop):
     1. Smart home devices — "IoT planters, sensors, controllers, custom hubs."
     2. Robotics — "Pick-and-place arms, mobile robots, custom actuators."
     3. Wearables — "Health trackers, fitness gear, prototype electronics."
     4. Custom tools — "Workshop fixtures, jigs, brackets, mounts."
     5. Maker projects — "Drones, weather stations, retro gaming consoles."
     6. Commercial prototypes — "Investor demos, Crowd Supply launches, hardware MVPs."
   - Each card: icon, title, one-line description, hover lift effect.

2. Use Motion for stagger fade-in on scroll.

3. Import and render <UseCases /> below <HowItWorks /> in src/app/page.tsx.
```

### Acceptance criteria
- Grid displays 6 cards in a clean responsive layout.
- Hover effect feels intentional (subtle lift or border highlight).
- Cards fade in as they enter the viewport.

### Test
Scroll past "How it works" — the use case grid should feel natural and concrete.

---

## PHASE 8 — Founder Section

### Goal
Add a personal section that builds trust by putting a human face on the project — critical for pre-launch credibility.

### What this phase delivers
A section with the founder photo, a 2–3 paragraph "why I'm building this," and a link to the vision memo.

### Dependencies
- Phase 7 complete
- A photo of you (headshot, doesn't need to be professional)
- The vision memo hosted somewhere (Notion public page, Google Doc, or your own /manifesto route)

### Tech & files
- New component `src/components/founder.tsx`
- Image asset in `public/founder.jpg`

### Implementation steps for Claude Code
```
1. Create src/components/founder.tsx:
   - Two-column layout on desktop, stacked on mobile:
     - Left: founder photo, rounded, max-w-md
     - Right: text content
   - Text content:
     - Eyebrow: "WHY THIS, WHY NOW"
     - Heading: "I've wanted to build hardware since I was a kid."
     - Paragraph 1: A condensed version of the personal story from the vision memo (2–3 sentences).
     - Paragraph 2: The "why now" — current AI capabilities making this possible.
     - Paragraph 3: One sentence call to action.
     - Link button: "Read the full vision →" linking to the vision memo URL.
   - All wrapped in a section with generous padding.

2. Place src/public/founder.jpg (the user supplies the actual image).

3. Use Next.js <Image /> for the photo with proper sizing.

4. Import and render <Founder /> below <UseCases /> in src/app/page.tsx.
```

### Acceptance criteria
- Section displays cleanly on desktop and mobile.
- Photo loads quickly (use `priority` if it's high in the page, otherwise lazy load).
- Vision memo link works.

### Test
Click the vision memo link — it should open the full document.

---

## PHASE 9 — FAQ Section

### Goal
Pre-empt the common objections that would otherwise prevent signup.

### What this phase delivers
An accordion of 5–7 FAQ entries answering the most likely visitor questions.

### Dependencies
- Phase 8 complete

### Tech & files
- shadcn/ui Accordion component
- New component `src/components/faq.tsx`

### Implementation steps for Claude Code
```
1. Install shadcn accordion:
   npx shadcn@latest add accordion

2. Create src/components/faq.tsx with these questions:
   Q1: "When will this be available?"
   A: "We're in private development. Waitlist members get access first when we open up — likely in early waves rather than a single launch."

   Q2: "Will the designs actually be manufacturable?"
   A: "Yes. The agent validates designs in physics simulation and against real component datasheets before you commit. Custom parts are routed to vetted fabrication partners with quality SLAs."

   Q3: "What kind of files will I get?"
   A: "STEP, STL, gerbers, BOM with sourcing links, firmware code, and a 3D assembly view. Everything you need to manufacture or hand off to a fab partner."

   Q4: "Do I need to know engineering or CAD?"
   A: "No. The agent handles component selection, schematic generation, mechanical design, and firmware. You describe what you want; it produces a buildable design."

   Q5: "Can I order the parts directly through the platform?"
   A: "Yes. Bill of materials links route to suppliers like Digikey and McMaster-Carr. Custom parts can be fabricated through partners and shipped to you."

   Q6: "Is this real or is it vaporware?"
   A: "We're early — pre-public-launch. We're sharing the vision now to build the right thing with the right people. The waitlist gets first access and shapes what ships."

   Q7: "Who's building this?"
   A: "[YOUR NAME] and a small team. Reach out at [YOUR EMAIL] if you want to talk."

3. Use the shadcn Accordion with type="single" collapsible behavior.

4. Section header:
   - Eyebrow: "QUESTIONS"
   - Heading: "Things people ask"

5. Import and render <FAQ /> below <Founder /> in src/app/page.tsx.
```

### Acceptance criteria
- All FAQs render in a clean accordion.
- Only one item open at a time.
- Smooth expand/collapse animation.

### Test
Click each question — verify the answer is correct and reads naturally.

---

## PHASE 10 — Footer & Repeated CTA

### Goal
Give scroll-deep readers a final chance to sign up and provide minimal navigation/credibility links.

### What this phase delivers
A repeated CTA section above the footer, plus a minimal footer with copyright, contact email, and social links.

### Dependencies
- Phase 9 complete

### Tech & files
- New components `src/components/cta-banner.tsx` and `src/components/footer.tsx`

### Implementation steps for Claude Code
```
1. Create src/components/cta-banner.tsx:
   - Full-width section with subtle gradient or border
   - Centered heading: "Be among the first to design with Cassen"
   - Subheading: "Pre-launch waitlist now open."
   - The same email signup form from the hero (reuse <SignupForm />)
   - Same trust line below

2. Create src/components/footer.tsx:
   - Minimal: just three rows
     Row 1: Cassen (small wordmark, left) | "Made with care" (right)
     Row 2: Links — Vision Memo | Contact | Twitter/X (when you have one)
     Row 3: "© 2026 Cassen. All rights reserved."
   - All small text, muted color (text-neutral-500)
   - Generous padding

3. Add both to src/app/page.tsx in order: <CTABanner /> then <Footer />.
```

### Acceptance criteria
- CTA banner appears at the bottom of the scroll, before the footer.
- Footer links work (vision memo, mailto for contact).
- Mobile layout is clean.

### Test
Scroll all the way down. The CTA should feel like a natural last call. Footer should look minimal and professional.

---

## PHASE 11 — Analytics Integration

### Goal
Track visits, conversions, and the email signup funnel.

### What this phase delivers
Three lightweight analytics tools wired up: Vercel Analytics for Core Web Vitals, Plausible for traffic, PostHog for funnel analysis and session replay.

### Dependencies
- Phase 10 complete
- Free Plausible account (or trial)
- Free PostHog account

### Tech & files
- `@vercel/analytics`, Plausible script, `posthog-js`
- Updates to `src/app/layout.tsx`, new `src/lib/posthog.ts`

### Implementation steps for Claude Code
```
1. Vercel Analytics:
   npm install @vercel/analytics
   Add <Analytics /> component to src/app/layout.tsx (in the body).

2. Plausible:
   - Create site at plausible.io for cassen.ai
   - Add the Plausible script tag to src/app/layout.tsx <head> via Next's <Script /> component
   - Use the simple snippet, not custom events for now

3. PostHog:
   npm install posthog-js
   - Create project at posthog.com
   - Add NEXT_PUBLIC_POSTHOG_KEY and NEXT_PUBLIC_POSTHOG_HOST to .env.local
   - Create src/lib/posthog.ts that initializes PostHog on the client
   - Wrap the app with a PostHogProvider (create a client component for this)
   - Track these events:
     - "landing_page_viewed" on first paint
     - "signup_form_focused" when email input gains focus
     - "signup_attempted" on form submit
     - "signup_succeeded" with position as property
     - "signup_failed" with error reason as property
     - "share_clicked" on share button click

4. In PostHog dashboard, create a funnel: viewed → focused → attempted → succeeded.
```

### Acceptance criteria
- Vercel Analytics shows page views (visible in Vercel dashboard).
- Plausible shows visitors in real-time.
- PostHog shows the events firing in the live events view.
- The funnel in PostHog shows real conversion data after a few signups.

### Test
1. Visit the site, fill in your email, submit.
2. Open PostHog → Live Events. You should see all 4 events fire in order.
3. Open Plausible. Your visit should appear within 30 seconds.

---

## PHASE 12 — Admin Dashboard

### Goal
A simple authenticated route where you can see the list of signups without opening Supabase.

### What this phase delivers
An `/admin` page protected by a hardcoded admin email check. Shows total signup count, most recent signups, and a CSV export button.

### Dependencies
- Phase 11 complete

### Tech & files
- New routes `src/app/admin/page.tsx` and `src/app/admin/login/page.tsx`
- Supabase Auth (magic link)
- Files: middleware updates, admin components

### Implementation steps for Claude Code
```
1. Enable Supabase Auth → Magic Link in Supabase dashboard.

2. Install @supabase/ssr if not already:
   npm install @supabase/ssr

3. Create src/middleware.ts that:
   - Checks if the route is /admin/*
   - If user is not signed in, redirects to /admin/login
   - If user is signed in but email doesn't match [ADMIN EMAIL] env var, returns 403

4. Create src/app/admin/login/page.tsx:
   - Email input + "Send magic link" button
   - On submit, call supabase.auth.signInWithOtp({ email })

5. Create src/app/admin/page.tsx (Server Component):
   - Use the service-role Supabase client to fetch from waitlist
   - Show total count, recent 50 signups, table with columns: position, email, created_at
   - "Export CSV" button (client component) that downloads all rows as CSV
   - Sign out button

6. Add ADMIN_EMAIL=[ADMIN EMAIL] to .env.local and to Vercel env vars.
```

### Acceptance criteria
- Visiting /admin while logged out redirects to /admin/login.
- Magic link email arrives and authenticates correctly.
- After login, the admin page shows the list.
- Visiting /admin from a different email is blocked with 403.
- CSV export downloads a valid file.

### Test
1. Visit /admin while logged out — should redirect.
2. Submit your admin email — receive magic link — click it — land on /admin.
3. See the signups list. Click Export CSV. Open the file — should be valid.
4. Sign out and try again with a different email — should be blocked.

---

## PHASE 13 — SEO, Meta Tags, and Final Polish

### Goal
Make sure the page looks right when shared on social, ranks for the right terms, and is fast.

### What this phase delivers
Open Graph image, structured meta tags, sitemap, robots.txt, performance optimizations, and final accessibility fixes.

### Dependencies
- Phase 12 complete

### Tech & files
- `src/app/layout.tsx` metadata
- `src/app/opengraph-image.tsx`
- `src/app/sitemap.ts`
- `src/app/robots.ts`

### Implementation steps for Claude Code
```
1. Update src/app/layout.tsx metadata with:
   - title (with template for sub-pages)
   - description
   - openGraph object: title, description, url, siteName, images, locale, type
   - twitter: card "summary_large_image", title, description, images
   - icons: favicon, apple-touch-icon
   - metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL)

2. Create src/app/opengraph-image.tsx using Next.js dynamic OG generation:
   - 1200x630
   - Dark background
   - Headline, Cassen wordmark
   - Same visual style as the hero

3. Create src/app/sitemap.ts that generates sitemap.xml with the home route.

4. Create src/app/robots.ts that allows all crawlers and references the sitemap.

5. Create a favicon set (use realfavicongenerator.net) and place files in /public.

6. Performance pass:
   - Audit with Lighthouse — target 95+ on all four scores
   - Compress all images
   - Remove unused dependencies
   - Verify all images use next/image
   - Check that no client components are doing heavy work above the fold

7. Accessibility pass:
   - All form inputs have labels (sr-only if visually hidden)
   - All interactive elements are keyboard reachable
   - Color contrast on all text meets WCAG AA (4.5:1 for body text)
   - prefers-reduced-motion respected on Motion animations

8. Final test on real devices: iPhone Safari, Android Chrome, desktop Chrome, desktop Safari.
```

### Acceptance criteria
- Sharing the URL on Twitter/X, LinkedIn, Slack shows the OG image and rich preview.
- /sitemap.xml and /robots.txt are accessible.
- Lighthouse scores 95+ on Performance, Accessibility, Best Practices, SEO.
- No console errors on page load.
- Form submission works on mobile Safari and Android Chrome.

### Test
1. Use opengraph.xyz to preview your URL — confirm the preview looks correct.
2. Run Lighthouse — confirm 95+ across the board.
3. Submit a signup from your phone — confirm end-to-end works.

---

## Summary of Phase Outputs

| Phase | Function delivered | Cumulative state |
|---|---|---|
| 1 | Project init + live URL | Placeholder page online |
| 2 | Hero section UI | Visually compelling page, no functionality |
| 3 | Email capture + database | Working signup, emails saved |
| 4 | Welcome email automation | New signups receive welcome email |
| 5 | Post-signup confirmation | Polished success state with position |
| 6 | "How it works" section | Visitors understand the product |
| 7 | Use cases grid | Visitors see concrete applications |
| 8 | Founder section | Trust through human story |
| 9 | FAQ section | Common objections answered |
| 10 | CTA banner + footer | Final conversion opportunity |
| 11 | Analytics | Real data on conversion funnel |
| 12 | Admin dashboard | Easy access to signups |
| 13 | SEO + polish | Shareable, fast, accessible |

---

## What This Document Doesn't Cover (Intentionally)

These belong to later versions of the landing page, not the pre-launch version:
- Pricing pages
- Login/signup for the actual product (you're not shipping the product yet)
- Documentation
- Blog
- Multi-language support
- A/B testing infrastructure beyond simple PostHog feature flags
- Referral mechanics with viral loops (add in v2 if waitlist takes off)

---

*End of document. Build phase by phase. Don't skip ahead.*