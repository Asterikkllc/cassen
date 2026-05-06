import type { SiteContent } from "./types";

export const DEFAULT_CONTENT: SiteContent = {
  meta: {
    title: "Cassen — Describe a product. Get a manufacturable design back.",
    description:
      "An AI agent for physical products. Skip months of CAD work — get DFM-ready designs, BOMs, and renders from a sentence.",
  },
  hero: {
    badge: "Pre-launch · Joining a private beta",
    headline: "Describe a product. Get a manufacturable design back.",
    subheadline:
      "For founders, makers, and product teams. Skip months of CAD work — get DFM-ready designs, BOMs, and renders from a sentence.",
    trust_line: "No spam. Just one email when access opens.",
  },
  founder: {
    eyebrow: "Why this, why now",
    heading: "I've wanted to build hardware since I was a kid.",
    paragraphs: [
      "The gap between “I have an idea for a thing” and “I have a thing” has always been months of CAD, datasheets, sourcing, and prototype hell. Most ideas don't survive that gap.",
      "The current generation of AI finally makes the whole pipeline tractable end-to-end — research, simulation, design, manufacturing prep — all from a sentence. That changes who gets to build physical products.",
      "Cassen is the agent I wished existed. If you build things, this is for you.",
    ],
    photo_url: null,
    photo_alt: "Founder portrait",
    vision_memo_url: "#",
    read_more_label: "Read the full vision",
    initials: "EO",
  },
  how_it_works: {
    eyebrow: "How it works",
    headline: "From sentence to shipped product",
    subhead: "Three steps. No engineering required.",
    steps: [
      {
        number: "01",
        icon: "MessageSquare",
        title: "Describe what you want to build",
        body: "A smart planter, a custom robot, a wearable — anything physical. Plain language, no jargon.",
      },
      {
        number: "02",
        icon: "Cpu",
        title: "Watch the agent design it",
        body: "Components researched, parts sourced, design assembled in 3D. Validated in physics simulation before you commit.",
      },
      {
        number: "03",
        icon: "Package",
        title: "Order the parts or the finished product",
        body: "Get a complete BOM with one-click ordering, or have the assembled prototype shipped to your door.",
      },
    ],
  },
  use_cases: {
    eyebrow: "Use cases",
    headline: "Built for everything physical",
    subhead: "From hobby projects to commercial products.",
    items: [
      {
        icon: "Home",
        title: "Smart home devices",
        body: "IoT planters, sensors, controllers, custom hubs.",
      },
      {
        icon: "Bot",
        title: "Robotics",
        body: "Pick-and-place arms, mobile robots, custom actuators.",
      },
      {
        icon: "Watch",
        title: "Wearables",
        body: "Health trackers, fitness gear, prototype electronics.",
      },
      {
        icon: "Hammer",
        title: "Custom tools",
        body: "Workshop fixtures, jigs, brackets, mounts.",
      },
      {
        icon: "Rocket",
        title: "Maker projects",
        body: "Drones, weather stations, retro gaming consoles.",
      },
      {
        icon: "Briefcase",
        title: "Commercial prototypes",
        body: "Investor demos, Crowd Supply launches, hardware MVPs.",
      },
    ],
  },
  faq: {
    eyebrow: "Questions",
    headline: "Things people ask",
    items: [
      {
        q: "When will this be available?",
        a: "We're in private development. Waitlist members get access first when we open up — likely in early waves rather than a single launch.",
      },
      {
        q: "Will the designs actually be manufacturable?",
        a: "Yes. The agent validates designs in physics simulation and against real component datasheets before you commit. Custom parts are routed to vetted fabrication partners with quality SLAs.",
      },
      {
        q: "What kind of files will I get?",
        a: "STEP, STL, gerbers, BOM with sourcing links, firmware code, and a 3D assembly view. Everything you need to manufacture or hand off to a fab partner.",
      },
      {
        q: "Do I need to know engineering or CAD?",
        a: "No. The agent handles component selection, schematic generation, mechanical design, and firmware. You describe what you want; it produces a buildable design.",
      },
      {
        q: "Can I order the parts directly through the platform?",
        a: "Yes. Bill of materials links route to suppliers like Digikey and McMaster-Carr. Custom parts can be fabricated through partners and shipped to you.",
      },
      {
        q: "Is this real or is it vaporware?",
        a: "We're early — pre-public-launch. We're sharing the vision now to build the right thing with the right people. The waitlist gets first access and shapes what ships.",
      },
      {
        q: "Who's building this?",
        a: "Evelyn Ogbodo and a small team. Reach out at hello@cassen.ai if you want to talk.",
      },
    ],
  },
  cta: {
    headline: "Be among the first to design with Cassen",
    subheadline: "Pre-launch waitlist now open.",
    trust_line: "No spam. Just one email when access opens.",
  },
  footer: {
    wordmark: "Cassen",
    tagline: "Made with care",
    vision_url: "#",
    vision_label: "Vision",
    contact_email: "hello@cassen.ai",
    contact_label: "Contact",
    twitter_url: "https://twitter.com",
    twitter_label: "X / Twitter",
    copyright_template: "© {year} Cassen. All rights reserved.",
  },
  signup: {
    email_placeholder: "you@company.com",
    submit_label: "Get early access",
    submit_pending_label: "Joining…",
    success_heading: "You're in.",
    success_position_template: "You're #{position} on the waitlist.",
    success_body:
      "We'll email when access opens. Until then, check your inbox — there's already a question for you.",
    share_label: "Share with someone who builds things",
    share_text:
      "Just joined the waitlist for Cassen — describe a product, get a manufacturable design back. cassen.ai",
    error_invalid_email: "Please enter a valid email.",
    error_duplicate: "You're already on the list.",
    error_generic: "Something went wrong. Please try again.",
    error_not_configured: "Signup is not configured yet. Please try again soon.",
  },
  welcome_email: {
    subject: "You're in. Welcome to Cassen.",
    greeting: "Hey,",
    position_line_template:
      "You just joined the waitlist for Cassen — thank you. You're #{position} in line.",
    body_paragraphs: [
      "We're building an AI agent that turns plain-language descriptions into manufacturable hardware designs. Think CAD, BOMs, firmware, all generated from a sentence.",
      "Quick question while it's fresh — what's the first physical product you'd describe to it? Hit reply and tell me. I read every response.",
    ],
    signature: "Evelyn, building Cassen",
    footer_disclaimer:
      "You're receiving this because you joined the Cassen waitlist. If this wasn't you, just ignore — we won't email again.",
  },
};
