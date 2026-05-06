Now we move on to real production development. You understand security/auth/endpoints/custom images and icons etc and what comprises of production enterprise level infrastructure. use the best practices# Cassen — v1 Product Requirements Document

**Product:** Cassen — AI Agent for End-to-End Physical Product Creation
**Domain:** cassen.ai
**Document type:** v1 / Launch PRD
**Status:** Defines the first publicly-launched version

---

## 1. Purpose of This Document

This PRD defines what Cassen ships at public launch. It is not a stripped-down MVP — it is the first serious, defensible release of a category-defining agentic product. Every capability listed here ships at launch.

A user lands on cassen.ai, signs in, describes a physical product in plain language, and receives a researched, validated, manufacturable design with parts ordered to their door — including custom-fabricated components and pre-flashed firmware. Companion app generation, deep research, and assembled prototype delivery are also live at launch.

The full long-term vision (multi-domain knowledge packs beyond electronics, mechanical, and fluids; OTA fleet management for shipped devices at scale; voice integrations; international compliance brokering at scale) is the domain of the final-product PRD. v1 ships the loop end-to-end with three knowledge packs and real fabrication.

---

## 2. v1 Goals

The first version is built to achieve four outcomes, in priority order.

**Demonstrate end-to-end magic at production quality.** A user describes a physical product and receives a working result they can hold in their hands within fourteen days. The agent must reliably produce manufacturable designs, validate them in physics simulation, source real parts, route custom fabrication, and ship.

**Establish category-defining differentiation.** No other platform combines cross-domain reasoning, physics-validated designs, real fabrication routing, generative 3D, firmware generation, and companion app generation in one experience. v1 ships all of these to claim the category.

**Generate sharable evidence.** Users post their built products on social channels with attribution back to Cassen. The platform produces shareable artifacts (3D viewer links, build videos, before/after demos) by default.

**Build the foundation for compounding moats.** Every project run feeds the simulation dataset, the parts grounding database, and the firmware template library. v1 architecture must be designed for these to compound across users from day one.

---

## 3. Target Users at Launch

v1 launches to two primary user segments simultaneously, with a secondary audience monitored for early signal.

**Primary — Hardware-curious creators.** Engineers, makers, designers, and product-curious technical professionals who want to ship physical products faster than current tools allow. Comfortable with technical concepts, willing to invest time in interesting tools, vocal advocates online when something works well. Includes Crowd Supply backers, Hackster contributors, Tindie sellers, Hackaday readers, and the broader maker-Twitter audience.

**Primary — Hardware startup founders.** Small teams shipping commercial hardware products who need cross-domain capability without hiring specialists in every discipline. Higher willingness to pay, higher project complexity, more public presence when products launch.

**Secondary — Educators and educational programs.** Universities, bootcamps, makerspaces, robotics competition teams. Lower revenue per seat but high concentration of future power users and viral testimonials.

General consumers, large enterprises, and regulated-industry users (medical, aerospace, defense) are not targeted at launch. They become priorities in subsequent versions.

---

## 4. Core User Journey

The user lands on cassen.ai and signs in with email or Google. They are presented with a single input: "Describe what you want to build." Suggested prompts orient new users — a smart planter, a delivery drone, a custom robotic arm, a wearable sensor, an industrial sensor enclosure.

The user states their goal in plain language. The agent acknowledges, asks clarifying questions only when truly necessary (a single follow-up question maximum), and begins working. The user watches in real time as the agent decomposes the goal, identifies relevant domains, and conducts research across electronics, mechanical, and fluids knowledge packs. Component reasoning, sourcing decisions, and design choices are visible as they happen — transparency is part of the magic.

The agent produces a complete design rendered in interactive 3D in the browser. Standard parts come from real CAD libraries (Digi-Key, McMaster mirror, GrabCAD). Custom mechanical parts are generated as parametric CAD scripts. Aesthetic or organic forms are handled through generative 3D. The user inspects the assembly, clicks individual components for specs, and asks the agent for alternatives or modifications in natural language.

The user runs the design in a physics sandbox. The agent auto-configures the simulation from the design itself — masses, motor torques, battery curves, material properties — and suggests test scenarios appropriate to the project. A drone gets hover, payload, wind, and failsafe tests. A robot gets drive, reach, stability, and battery tests. The user watches the simulation run in real-time 3D, can intervene mid-test, and reviews agent analysis in plain language. Issues are identified, fixes proposed, and the user accepts changes with a click.

When the design passes simulation, the user reviews the bill of materials. Live pricing comes from Nexar's multi-distributor aggregator. Standard parts route through Digi-Key, Mouser, LCSC, and the curated McMaster mirror. Custom mechanical parts route through Xometry (CNC, sheet metal, 3D print), JLCPCB (3D print, PCB), or SendCutSend (sheet metal). PCBs route through JLCPCB with component pre-population for SMT assembly. The user clicks to order, pays through Stripe, and the platform splits and routes the order across suppliers.

The agent generates firmware tailored to the chosen microcontroller using PlatformIO with Zephyr or ESP-IDF templates. The firmware ships pre-flashed to the assembled hardware where applicable. The agent generates a Progressive Web App companion controller from the project's interaction schema — sliders, buttons, sensor readouts, telemetry, camera feeds — accessible via QR code paired to the device.

The user can export every artifact: STEP, STL, gerbers, BOM, firmware source, and 3D assembly views. Files render in the browser viewer and download cleanly for users who want to fabricate elsewhere.

For users without their own assembly capability, Cassen offers fully assembled prototype delivery through partner fulfillment. The user receives the working product, charges it, opens the companion app, and uses it.

For users with serious commercial intent, deep research mode produces a comprehensive engineering report with multi-pass component sourcing, lifecycle analysis, FMEA, DFM review, FCC/CE/UN 38.3 pre-screening, and Monte Carlo tolerance simulation. Output is a long-form PDF suitable for sharing with co-founders, investors, or manufacturing partners.

---

## 5. In-Scope Capabilities for v1

### 5.1 AI Reasoning & Agent Core

The orchestration core uses LangGraph (Python) for graph-based durable execution with checkpointing, resume-on-failure, and human-in-the-loop interrupts. Multi-agent topology includes a top-level planner, a research agent, domain-specific design agents (electronics, mechanical, fluids), a simulation agent, a sourcing agent, a firmware agent, and a companion-app agent. Tools are exposed through Model Context Protocol (MCP) servers, ensuring portability and reuse.

The agent operates with thoughtful clarifying behavior — at most one follow-up question per session, and only when truly necessary. Default behavior is to make reasonable assumptions, communicate them clearly, and let the user revise.

Three knowledge packs ship at launch: electronics (microcontrollers, sensors, power, communications), mechanical (enclosures, brackets, frames, mounts, simple linkages), and fluids (pumps, valves, basic hydraulic and pneumatic systems). Each pack is implemented as an MCP server with curated component libraries, design heuristics, and validation rules.

Cross-domain reasoning is a first-class capability. Projects spanning all three domains — for example, a smart planter combining electronics, a 3D-printed enclosure, and a water pump — are handled in a single coherent design pass.

Vector grounding uses pgvector on Supabase or Neon, indexing component datasheets, KiCad libraries, GrabCAD STEP files, and McMaster catalog entries. Live web search augments structured data through the Firecrawl agent endpoint.

Models in production: Claude Opus 4.7 as the primary reasoning model, with Claude Sonnet 4.6 for cost-sensitive sub-agent tasks and OpenAI o-series as a fallback. Long-running jobs run on Trigger.dev v3 workers with no timeout caps. Observability is provided by Langfuse with full trace context.

### 5.2 Component Sourcing

Cassen uses a three-tier cascade for every component in a design.

The first tier fetches from real CAD libraries and supplier APIs. Digi-Key Product Information API and Mouser Search API provide canonical electronics components with full specifications, datasheets, lifecycle status, and pricing. Nexar's GraphQL API aggregates multi-distributor data including LCSC. JLCPCB Components API serves the assembly-aware path when boards will be produced through JLC. Mechanical components come from a curated McMaster mirror — five thousand of the most commonly referenced parts maintained as STEP files with full metadata, refreshed weekly. GrabCAD provides supplementary mechanical hardware. KiCad libraries provide schematic symbols and PCB footprints.

The second tier generates parametric CAD geometry through Build123d (Python on Open Cascade BREP) for custom mechanical parts — enclosures, brackets, mounts, frames, panels. Output is precise, manufacturable, editable, and exportable as STEP for CAD or STL for 3D printing. OpenSCAD remains available for one-shot procedural generation when scripting is more natural than parametric modeling.

The third tier invokes generative 3D for organic, aesthetic, or novel shapes that cannot be fetched or scripted. Hyper3D Rodin Gen-2 is the primary engine for high-quality outputs. Trellis 2 and Hunyuan3D 3.5 serve as cost-efficient alternatives. Generative output is used for visualization and concept; manufacturable parts always route through tier one or tier two.

The agent decides per-component which tier applies, with a deterministic preference order: fetch first, parametric second, generative last. Component grounding ensures the agent references real, available parts — no hallucinated SKUs — through retrieval-augmented selection over the live parts database.

### 5.3 3D Visualization

Browser-based 3D rendering uses Three.js with the WebGPU renderer (r171+, fallback to WebGL2 where unsupported), wrapped in React Three Fiber v9 for declarative React integration. The drei utility library, react-three-postprocessing, and react-three-rapier provide ergonomics, post-effects, and inline collision visualization.

Users see the complete product assembled with components nested correctly — boards inside enclosures, motors mounted to frames, wiring routed. They rotate, pan, zoom, click any part to see specifications, and ask the agent for alternatives or modifications without leaving the viewer.

STEP files render through server-side conversion to GLTF using Open Cascade Python bindings — STEP is too heavy for client-side rendering at scale. STL and GLTF render through Three.js native loaders. The viewer is mobile-responsive with touch controls calibrated for production use.

Real-time collaboration on the 3D scene is powered by Liveblocks Yjs, enabling multiple users in the same project room with synchronized state, presence indicators, and cursor sharing.

### 5.4 Physics Sandbox Simulation

NVIDIA Newton 1.0 is the primary physics engine, integrated through the MuJoCo Warp backend and Disney Research's Kamino solver for closed-loop mechanisms. Simulation runs on GPU pods provisioned through Modal — RTX 6000 Blackwell or H100 — orchestrated by Trigger.dev workers that scale on demand.

Physics coverage at launch spans rigid body dynamics, kinematic chains, manipulation, electrical and circuit simulation through ngspice via PySpice, and basic thermal modeling. Aerodynamics uses PyBullet for fast drone-loop iteration; OpenFOAM batch CFD is available for deep research mode.

Auto-configuration translates designs to runnable physics scenes without user intervention. Component masses come from datasheets and library metadata. Motor torque curves come from manufacturer specifications. Battery discharge profiles come from cell datasheets. Material properties (density, friction, restitution) come from a curated library tied to the parts database. STEP-to-MJCF conversion uses Build123d-derived transforms with onshape-to-robot-style patterns adapted for Cassen's component metadata.

The agent recommends test scenarios appropriate to the project type. A drone gets hover, payload, wind, failsafe, and battery-life tests. A robot gets drive, reach, grip, stability, and battery tests. A planter gets watering schedule, soil-moisture-response, and battery-life tests. The user runs scenarios with one click and watches in real-time 3D, can pause and intervene, and reviews agent analysis in plain language.

Every simulation run is captured to the platform dataset — outcomes, parameters, design context — feeding the long-term agent improvement flywheel.

### 5.5 Firmware Generation

Firmware generation targets ESP32-family (via ESP-IDF 5.5+), STM32 and Nordic nRF (via Zephyr), Raspberry Pi RP2040 and RP2350 (via Pico SDK), and Arduino-family devices (via Arduino Core 3.3+ for rapid prototyping flows). PlatformIO is the build substrate.

Knowledge packs emit Zephyr-style devicetree overlays plus a generated `main.c` or `main.cpp` from templated subsystem blocks (sensor read loops, motor control with PID, BLE/Wi-Fi/MQTT communication, power management, safety checks). Code is generated from validated templates — never from scratch — and tested in CI against hardware-in-the-loop stubs before being flashed.

Firmware is signed with MCUboot and pre-flashed to delivered hardware where the platform handles assembly. For self-assembled hardware, users receive the firmware source and a one-line build-and-flash command.

Over-the-air update infrastructure for delivered devices is provided through Golioth — Zephyr-native, ships logging, settings, metrics, OTA, and device-cloud connectivity in a single SDK.

### 5.6 Companion App Generation

Every project that requires user interaction receives a generated companion app. The default is a Progressive Web App (Next.js 16 + React 19 + shadcn/ui on Tailwind v4), accessible via QR code that pairs the device to the user's account. No installation required. Works on iOS and Android through PWA install with push notifications enabled.

The agent generates UI from the project's interaction schema — virtual joysticks, sliders, buttons, toggles, sensor displays, camera feeds, telemetry, and history charts. Users describe what controls they want during the design phase and the agent assembles the interface accordingly. shadcn/ui components ensure design consistency across all generated apps.

Communication protocols include MQTT over WSS for cloud-controlled devices, Web Bluetooth for direct BLE pairing, and WebSerial for desktop USB-tether flows. The strict device-app protocol layer is defined in a JSON schema that both the firmware generator and the app generator consume — guaranteeing consistency between hardware and software sides.

For projects requiring native capabilities beyond PWA (background tasks, deep BLE features), Expo with React Native serves as the fallback path.

Voice and smart-home integrations (Alexa, Google Assistant, Siri Shortcuts) are not in v1. They ship in v2.

### 5.7 Parts Marketplace

Bills of materials produced by the agent route through a custom marketplace layer. Nexar GraphQL provides multi-distributor aggregation for component pricing and availability. Digi-Key and Mouser REST APIs handle direct fulfillment for electronics. JLCPCB Components API handles the integrated PCB-plus-assembly path with single-shipment economics. The McMaster mirror serves mechanical hardware — five thousand curated parts with weekly refresh, ordered through authenticated affiliated cart redirects.

BOM splitting logic minimizes the number of unique distributors per order, prefers in-stock parts with active lifecycle status, and falls back to manufacturer-recommended substitutes when primary parts are unavailable. The user sees a single price-and-lead-time matrix and clicks once to order.

Multi-vendor checkout uses Stripe Connect for US, EU, and UK fulfillment. Paystack and Flutterwave handle African geographies. Order routing chooses payment processors based on buyer location to minimize fees and currency conversion friction.

Order tracking uses AfterShip's unified multi-carrier API. Returns and replacements are managed through a single platform interface — users never deal with individual supplier accounts.

### 5.8 Custom Fabrication Routing

Custom fabrication is routed through partner APIs based on material, finish, lead time, and budget. The agent picks the appropriate partner per part automatically, with the user seeing a unified order experience.

3D printing in plastic (FDM, SLA, MJF) routes primarily through JLCPCB 3D Printing for Asia-region cost efficiency, Xometry for US lead times, and PCBWay for broader material options. Plastic materials at launch include PLA, PETG, ABS, SLA resin (multiple grades), and MJF nylon.

3D printing in metal (DMLS in stainless, aluminum, titanium) routes through Xometry. Metal printing is offered but with longer lead times and higher prices clearly displayed.

CNC milling routes primarily through Xometry (US) and JLCPCB CNC (Asia). Materials at launch include aluminum 6061, aluminum 7075, mild steel, stainless 304, brass, and Delrin.

Sheet metal cutting and bending routes through SendCutSend (US, fastest), OSH Cut (US, automatic feature detection and 3D bend simulations, broader material library), and Xometry (international). Materials include aluminum, mild steel, stainless, copper, and brass at standard thicknesses up to one half inch.

Laser cutting follows the same routing as sheet metal.

PCB fabrication routes through JLCPCB (default — best price, integrated assembly), with PCBWay and OSH Park available for users who explicitly select alternatives. PCB output produces Gerber X2, Excellon drill files, and IPC-2581 for advanced workflows. Pick-and-place CSVs are generated in JLC's coordinate convention for SMT assembly.

Injection molding for production runs is not in v1 — it ships in v2 once the platform has volume to justify tooling investments.

Quality is guaranteed through SLAs with each fabrication partner. Reprints and replacements are handled by Cassen with the partner billed back. A unified post-delivery support flow lets users flag issues without identifying which supplier produced which part.

Users with their own machines can export clean STL, STEP, DXF, and G-code files for self-fabrication at no additional cost.

### 5.9 On-Demand Assembled Prototypes

Users who want the finished product without assembling it themselves can opt for full assembly delivery. The platform routes assembly through MacroFab (US, traceability-grade), JLCPCB SMT Assembly (integrated electronics), and white-label mechanical assembly partners (Sourcify and Cody Engineering in the US; PCBWay-coordinated partners in Shenzhen).

Assembly tooling and instructions are generated from the design — exploded views from STEP via Open Cascade, layered PDF assembly steps, and pick-and-place CSVs for PCB assembly.

Quality control uses third-party inspection through InstaQC or AQF for Asia-produced units. Photographic QC reports are generated for every assembled prototype.

Shipping is managed through EasyPost or Shippo with automatic customs documentation, HS code lookup, and signed-off product liability insurance bundled per shipment via Hiscox or Coalition for Commercial.

Documentation, instructions, and warranty information are included with every assembled prototype delivery.

### 5.10 Deep Research Mode

Deep research is a premium tier of investigation that goes substantially beyond standard agent depth. Users opt in per project for serious commercial-intent designs.

Multi-pass component sourcing evaluates dozens of alternatives per component across cost, lead time, minimum order quantity, lifecycle status, and obsolescence risk. Lifecycle data comes from Octopart's Nexar Lifecycle API and is enriched with manufacturer PCN and EOL feeds where available.

Datasheet PDFs are read in full and cross-referenced — including PDF parsing of complex tables and figures — through LlamaParse Agentic Plus mode for primary parsing and Reducto for multi-pass agentic OCR with citation-level provenance.

Failure mode and effects analysis is generated by a LangGraph subgraph that walks the BOM, enumerates failure modes per component, scores severity, occurrence, and detection, and proposes mitigations. Output is structured FMEA tables suitable for engineering review.

Compliance pre-screening covers FCC Part 15 envelope checks (algorithmic), CE EMC pre-screening, RoHS BOM screening, REACH SVHC checks, and UN 38.3 battery shipping pre-screening. Full certification booking through partner labs (Intertek, TÜV SÜD, Element, MiCOM) is available as a paid add-on routed through Cassen's compliance broker layer.

Monte Carlo simulation runs hundreds of variations across temperature ranges, manufacturing tolerances, and edge case conditions on the Modal GPU pool.

Design for Manufacturing review uses Xometry's API DFM endpoint, JLCPCB's DFM tool, and PCBWay DFM in parallel for redundant feedback. KiCad ERC and DRC are invoked headlessly via `kicad-cli` for schematic and PCB validation.

Output is a long-form PDF engineering report rendered through Typst (modern Rust-based LaTeX replacement) suitable for sharing with co-founders, investors, or manufacturing partners. Three.js renders are embedded as PNG snapshots.

### 5.11 Project Management & Collaboration

Projects are saved with full version history. Users fork, branch, and revert designs with Git-LFS-style semantics on top of immutable Cloudflare R2 blob storage. Yjs document IDs serve as version refs with periodic snapshots.

Real-time collaboration is powered by Liveblocks Yjs. Multiple users in the same project room see synchronized state, presence indicators, and cursor positions. Comments and review tools are first-class.

Workspaces and role-based access use Clerk for consumer authentication and WorkOS for enterprise SSO and SCIM. Roles map to Liveblocks room permissions.

Public sharing produces a read-only URL with embeddable 3D viewer. Anyone with the link views the project but cannot edit. Forking from public projects is one click. A template library indexed on pgvector enables natural-language project search ("show me drone projects under $200 BOM").

### 5.12 Onboarding & First-Project Experience

A library of fifteen production-ready example projects ships at launch, each spanning at least two of the three knowledge packs. Examples include a smart planter (electronics + mechanical + fluids), a delivery drone (electronics + mechanical), a custom robotic arm (electronics + mechanical), a wearable health sensor (electronics + mechanical), an industrial environmental sensor (electronics + mechanical + enclosure), a desktop weather station, a soldering fume extractor, an automated pet feeder, a custom mechanical keyboard, a portable PCB design lab, and several others.

Users fork any example as a starting point. A guided walkthrough on first project surfaces key features without being intrusive — three pop-ins maximum, dismissible and skippable.

---

## 6. Explicitly Out of Scope for v1

The following ship in subsequent versions and are explicitly excluded from v1.

- Knowledge packs beyond electronics, mechanical, and fluids (chemistry, optics, textiles, woodworking, biology, etc.)
- Voice and smart-home integrations (Alexa, Google Assistant, Siri)
- Multi-device sync, cloud automation, and scheduling for shipped devices
- WebXR / AR / VR viewing
- Native mobile applications (PWA only at launch)
- Injection molding routing
- International compliance brokering at scale (FCC, CE, UL pre-screening only — full lab booking is paid add-on)
- Enterprise on-premise or VPC deployment
- White-label and embedding for third-party platforms
- Custom physical controller hardware design (printed handhelds with screens)
- Advanced computer vision and ML for vision-enabled robots

---

## 7. Technical Stack — Locked In

### 7.1 Reasoning & Agent Layer

LangGraph (Python) for graph orchestration with durable execution and checkpointing. Anthropic MCP for tool exposure. Claude Opus 4.7 as primary reasoning model. Claude Sonnet 4.6 and OpenAI o-series as cost-tier and fallback models. Trigger.dev v3 for long-running jobs. Langfuse for observability.

### 7.2 Component Sourcing

Digi-Key Product Information API, Mouser Search API, Nexar GraphQL (multi-distributor), JLCPCB Components API, KiCad libraries, GrabCAD Library, custom McMaster-Carr mirror (five thousand curated SKUs, weekly refresh).

### 7.3 CAD Generation

Build123d (Python, Open Cascade BREP) as primary parametric engine. CadQuery for legacy compatibility. OpenSCAD for one-shot scripts. Manifold (npm `manifold-3d`) as the mesh kernel. SKiDL and tscircuit for circuit-as-code generation. KiCad invoked headlessly via `kicad-cli` for schematic and PCB workflows.

### 7.4 Generative 3D

Hyper3D Rodin Gen-2 as primary high-quality engine. Trellis 2 and Hunyuan3D 3.5 as cost-efficient alternatives.

### 7.5 Visualization

Three.js with WebGPU renderer. React Three Fiber v9. drei, react-three-rapier, react-three-postprocessing.

### 7.6 Physics Simulation

NVIDIA Newton 1.0 as primary engine. MuJoCo Warp backend. Disney Research Kamino solver for closed-loop mechanisms. PyBullet for fast drone iteration. ngspice via PySpice for circuit simulation. OpenFOAM for batch CFD (deep research only). GPU compute on Modal (RTX 6000 Blackwell or H100). Trigger.dev orchestration.

### 7.7 Firmware

PlatformIO as build substrate. ESP-IDF 5.5+ for ESP32. Zephyr for STM32 and Nordic. Pico SDK for RP2040 and RP2350. Arduino Core 3.3+ for rapid prototyping flows. MCUboot for image signing. Golioth for OTA and fleet management.

### 7.8 Companion Apps

Next.js 16 with App Router and Turbopack. React 19 with React Compiler. Tailwind v4. shadcn/ui components. PWA-first delivery. Expo (React Native 0.79+) for native fallback.

### 7.9 Marketplace & Logistics

Stripe Connect for US, EU, UK payments. Paystack and Flutterwave for Africa. AfterShip for unified order tracking. EasyPost or Shippo for shipping label generation and customs.

### 7.10 Fabrication Partners

Xometry, JLCPCB, PCBWay, SendCutSend, OSH Cut, MacroFab, Sourcify, Cody Engineering, InstaQC, AQF, Hiscox / Coalition for Commercial (liability insurance bundled per shipment).

### 7.11 Compliance (Pre-Screening + Broker)

Algorithmic FCC Part 15 envelope checking. RoHS / REACH BOM screening. UN 38.3 battery shipping pre-screening. Full certification booking routed through Intertek, TÜV SÜD, Element, MiCOM Labs.

### 7.12 Deep Research

LlamaParse Agentic Plus for primary PDF parsing. Reducto for high-accuracy multi-pass parsing. Octopart Nexar Lifecycle for component lifecycle data. Typst for PDF report rendering.

### 7.13 Collaboration

Liveblocks Yjs for real-time collaboration. Yjs for CRDT semantics. Cloudflare R2 for immutable artifact storage. Cloudflare D1 and KV for edge state. PartyKit (Cloudflare) as self-hostable fallback.

### 7.14 Platform Infrastructure

Frontend: Next.js 16, React 19, Tailwind v4, shadcn/ui. Deployment on Vercel. Backend: Python (FastAPI) for agent core, Node.js (Hono on Cloudflare Workers) for edge endpoints. Database: Supabase Postgres (or Neon for serverless branching) with pgvector 0.7+. Object storage: Cloudflare R2. Auth: Clerk (consumer) and WorkOS (enterprise). Compute orchestration: Trigger.dev v3 for jobs, Modal for GPU. Observability: Langfuse (LLM), Sentry (errors), PostHog (product analytics, feature flags, session replay). CI/CD: GitHub Actions, Vercel Deploy, Modal for Python services.

### 7.15 Data & Learning

Every project run, simulation, and design outcome captured to Postgres + R2. Tagged by project ID and outcome (shipped, cancelled, failed-DFM). DVC or LakeFS for data versioning. Weekly batch fine-tunes via OpenAI fine-tuning or Together.ai on success/failure pairs. Argilla for structured human evaluations. Thumbs-up and thumbs-down feedback on every agent artifact, captured in Langfuse with full trace context.

---

## 8. Success Criteria for v1

v1 is considered successful if it meets the following thresholds.

**Activation.** Forty percent of signups create a project. Sixty percent of projects reach the bill of materials view rather than abandoning mid-design.

**Demo virality.** Organic posts (Twitter/X, Reddit, YouTube, Hacker News) reaching significant unprompted reach (fifty thousand or more views or front-page Hacker News).

**Transaction signal.** At least ten percent of active users complete a parts order within their first session. At least two percent of active users complete a custom fabrication order.

**Quality bar.** Order success rate (parts fit and work as designed) at or above ninety percent. Return rate below five percent. Average time from prompt to first viable design below five minutes for projects within the three knowledge packs.

**Qualitative.** Users describe the experience as "magical," "category-defining," or equivalent in feedback messages and reviews.

---

## 9. What v1 Sets Up for Later Versions

v1 establishes the core infrastructure that every future capability builds on: the LangGraph + MCP agent core, the parts grounding database, the three-tier sourcing pipeline, the Three.js visualization layer, the Newton physics infrastructure, the firmware generation pipeline, the companion app generator, the marketplace routing engine, and the fabrication partner network.

The simulation dataset, project outcomes database, and parts grounding corpus begin compounding from day one. Every project teaches the system to design better next time, recommend better parts, and predict failure modes.

Future versions add additional knowledge packs (chemistry, optics, textiles, woodworking, biology), voice and smart-home integrations, native mobile, WebXR, injection molding routing, full international compliance brokering, enterprise deployment, and white-label embedding — all on top of the v1 substrate without architectural rewrites.

---

*End of document.*