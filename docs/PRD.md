# Product Requirements Document — Final Product

**Product:** Cassen — AI Agent for End-to-End Physical Product Creation
**Domain:** cassen.ai
**Document type:** Final-state vision PRD
**Status:** Defines the complete, fully realized product

---

## 1. Product Overview

Cassen is a general-purpose AI agent that lets anyone — engineers and non-engineers alike — describe a physical product in natural language and receive a complete, working result: design, validation, parts, firmware, app, and optionally the fully assembled product shipped to their door.

The user states a goal; the system handles every step from research to working product. Where AI lowered the floor for software creation, Cassen lowers the floor for hardware and every other physical discipline.

The product covers any physical project — drones, robots, smart home devices, furniture, planters, scientific instruments, custom tools, wearables, and anything else a user can describe. It does not specialize in any single vertical.

---

## 2. Vision Statement

Cassen makes it as easy to ship physical products as it is to ship software.

Anyone with an idea should be able to bring it into the physical world — without engineering training, CAD skills, electronics knowledge, or programming experience. Cassen is the bridge between human imagination and physical reality. It removes every traditional barrier: research, design, validation, sourcing, fabrication, software, and assembly.

The platform serves both ends of the spectrum: casual creators who want a working gadget without learning anything new, and serious engineers and founders who need real depth and rigor when the stakes demand it.

---

## 3. Target Users

The product serves five primary user segments:

**General consumers.** People with ideas but no engineering background. Want to ship working products without learning new skills. Largest addressable segment.

**Makers and hobbyists.** Existing maker community seeking to accelerate workflow and reduce friction. Tech-comfortable but want results faster than current tools allow.

**Hardware startup founders.** Small teams building physical products who need cross-domain capability without hiring specialists in every discipline.

**Educators and students.** Universities, bootcamps, makerspaces, and individual learners using the platform for hands-on creative and technical education.

**Small product teams in established companies.** Internal tools, rapid prototyping, custom fixtures, and exploratory R&D.

---

## 4. Core User Journey

The user states a goal in plain language: "I want a small robot that picks up my dog's toys," or "I need a smart planter that waters my herbs based on soil moisture."

The agent decomposes the goal into required components and capabilities, conducts research across electronics, mechanical, software, and any other relevant domains, and assembles a complete design.

The user sees the design rendered in interactive 3D — a holographic-style assembly of every part with full visibility into how components connect. They can rotate, inspect, and ask questions about any element.

The user runs the design in a physics sandbox. Their drone flies in simulated wind. Their robot drives across simulated floors. Their planter waters virtual plants. The agent identifies issues — insufficient torque, tipping risk, battery undersizing — and suggests fixes the user can accept with one click.

Once the design passes simulation, the user reviews the bill of materials with live pricing across suppliers. They click order. The platform routes parts across multiple suppliers, fabricates any custom components, and ships everything in a single consolidated delivery.

The agent also delivers firmware pre-flashed to the microcontroller and a companion app — a phone or web interface for controlling the product. The user opens the box, charges the device, opens the app, and the product works.

For users who prefer not to assemble, the platform offers a fully assembled prototype delivered ready-to-use.

For users with serious commercial intent, a deep research mode produces a comprehensive engineering review covering compliance, manufacturing, failure modes, and lifecycle considerations.

---

## 5. Functional Capabilities

### 5.1 AI Design Agent

The reasoning core that turns goals into designs. Capable of decomposing arbitrary user goals into component trees, identifying which domains apply, conducting research across web sources and structured component databases, and validating feasibility before committing to a design.

The agent is built on a domain-agnostic core with a knowledge pack architecture. Knowledge packs are modular expertise modules covering specific domains: electronics, mechanical engineering, chemistry, software, furniture, plumbing, optics, fluids, textiles, woodworking, and others. Packs are added over time and the user never sees them — the agent loads relevant ones based on the project.

Cross-domain reasoning is a first-class capability. Projects spanning electronics plus mechanical plus software are handled in a single coherent design pass.

### 5.2 Component Sourcing Pipeline

Every component in a design is sourced through a cascading three-tier approach.

The first tier is fetching existing CAD models from libraries like GrabCAD, McMaster-Carr, manufacturer datasheets, Digikey, and others. Standard parts are pulled directly with full specifications and verified compatibility.

The second tier is parametric generation. For configurable components — custom enclosures, brackets, frames, mounts — the agent writes parametric CAD scripts (using CadQuery, OpenSCAD, or Build123d) that produce exact geometry on demand. Output is precise, manufacturable, and editable.

The third tier is generative AI 3D. For organic, novel, or aesthetic shapes that cannot be fetched or scripted, the agent invokes generative models (Meshy, Rodin, Tripo, Hunyuan3D, or successors). Used as a fallback when precision is not the priority.

The platform integrates live supplier data for pricing, availability, lead time, and lifecycle status, ensuring designs reference parts that actually exist and can be obtained.

### 5.3 The Workshop — Live Assembly Environment

The Workshop is the spatial environment where users watch the agent assemble their product from real parts. It is not a static 3D view — it is a lifelike workshop space where assembly happens in front of the user.

Every component is a real CAD file with full geometry. Standard parts come from real libraries with exact dimensions, mounting features, and material properties. Custom parts are generated parametrically with mating relationships designed in from the start — the agent doesn't snap arbitrary parts together, it designs every part to fit every other part by construction. An enclosure is generated with mounting holes that match the chosen PCB. A battery compartment is sized exactly for the chosen battery. A motor mount is designed around the specific motor's bolt pattern.

Visual fidelity is photorealistic by default. Real materials look real — brushed aluminum reflects like brushed aluminum, ABS plastic shows its sheen and surface texture, FR4 PCB substrate shows its layer stack and silkscreen, anodized parts show anodization color and grain, glass diffuses and refracts, wood shows grain and finish, fabric drapes and creases. Lighting is real with global illumination, soft shadows, and physically-accurate light propagation. Reflections are real. Surfaces have weight, micro-detail, and the imperfections that make manufactured objects look manufactured.

Photoreal rendering runs through a hybrid pipeline. Real-time interaction uses physically-based rendering (PBR) with WebGPU — real materials, real lighting, real shadows at interactive frame rates. When the user pauses to inspect or wants a marketing-quality view, the platform invokes cloud-rendered ray tracing through NVIDIA Omniverse and streams the result back as a high-resolution image or video. The transition is seamless — interactive view for working, photoreal view for sharing, both showing the same product with the same materials and the same lighting.

For users who want to share their product publicly — Crowd Supply campaigns, Kickstarter videos, investor pitches, social posts — the platform generates photoreal hero shots, animated turntables, exploded views, and product-in-context renders (the planter on a windowsill, the drone in a sky, the robot in a living room) on demand.

The user can rotate, zoom, inspect any part at any level of detail, click for full specifications, and ask the agent for alternatives or modifications in natural language. They can pause assembly mid-process to inspect intermediate states. They can request exploded views, cross-sections, and dimensional callouts on demand.

### 5.4 The Test Room — Lifelike Physics Sandbox

The Test Room is where assembled products come alive. It is a 3D sandbox of real-world physics where users place their product and watch it behave as it would in physical reality.

Environmental controls let users configure conditions the product will face. Wind speed and direction. Ambient temperature. Humidity. Surface friction (carpet, hardwood, concrete, grass, water). Gravity (Earth-default, optional Mars or Moon for fun). Time-of-day lighting. Obstacles and terrain. Water levels for floating or watering tests. Wireless interference for testing communication-dependent products. The Test Room is not a generic physics demo — it is a configurable representation of the real environments the product will actually be used in.

Physics coverage spans rigid body dynamics, kinematic chains, contact and friction, motor response, basic aerodynamics, water and basic fluid behavior, electrical and circuit behavior, thermal modeling, and structural loads. Real-time physics handles what matters for live interaction — drive, lift, balance, motor response, contact, basic wind effects. Heavier physics requiring computational fluid dynamics, full finite element analysis, or detailed electromagnetic simulation are available in deep research mode as precomputed scenarios.

The user enters the Test Room with their assembled product, sets the environmental conditions, and presses play. The product behaves according to physics. A drone responds to throttle inputs with real lift, drift in real wind, drains its battery according to real current draw under load. A robot drives across the configured surface at speeds limited by motor torque and surface friction, tips over if its center of gravity exceeds its base of support. A smart planter senses real soil moisture (configurable), waters real virtual plants on a real schedule, runs out of battery on a realistic timeline based on its actual current draw. A wearable reads real simulated biometric data based on configured user activity.

The agent analyzes results in plain language and proposes fixes the user accepts with a click. The user can pause mid-test, change conditions, rewind, branch into alternative scenarios, and run side-by-side comparisons of design variations.

Every Test Room session is captured to the platform dataset — outcomes, parameters, design context, environmental conditions — feeding the agent improvement flywheel and giving users a permanent record of what they tested and what they found.

### 5.5 The Unified Runtime — One Control Protocol for Everything

The Unified Runtime is the technical innovation that makes the Workshop, the Test Room, the companion app, controllers, and real shipped hardware behave identically.

When the agent designs a product, it generates a single control protocol — a structured schema describing every input the product accepts and every output it produces. This schema drives four parallel implementations simultaneously:

The **simulation runtime** in the Test Room responds to inputs according to the protocol, producing physics-accurate outputs.

The **companion app** is generated from the same protocol — sliders, joysticks, buttons, telemetry displays, camera feeds — and accessible via a custom URL the user shares with anyone (e.g., cassen.ai/p/[project]/control). Open the URL on a phone, control the simulated product. Receive the real product, open the same URL, control the real one. No installation. No app store.

The **input mappings** for keyboard and controllers are also generated from the protocol. PC users get a WASD or arrow-key control scheme that makes sense for the product. Gamepad users plug in any standard controller (Xbox, PlayStation, Switch Pro, generic) and the Cassen runtime auto-maps the protocol to the controller's inputs through the Web Gamepad API. Users with custom-built controllers (made through Cassen or elsewhere) connect them and the runtime adapts.

The **firmware** running on the real product is generated from the same protocol, ensuring that pressing "forward" in the Test Room produces identical behavior to pressing "forward" on the real device. There is no separate "sim mode" and "real mode" — they are the same code paths driven by the same schemas, running in the cloud during testing and on the microcontroller after delivery.

The user experience is seamless. They design in the Workshop. They test in the Test Room with their phone, keyboard, or controller. The product gets fabricated and shipped. They open the same companion app URL or pick up the same controller, and the real product behaves exactly as the simulated one did. No relearning. No surprises. No firmware-versus-app mismatches.

### 5.6 Firmware Generation

Firmware for the physical product is generated from the same Unified Runtime protocol described in 5.5. This ensures the real shipped product behaves identically to the simulated one tested in the Test Room.

Firmware targets the chosen microcontroller — ESP32, Arduino, Raspberry Pi, STM32, RP2040, RP2350, and others. The agent selects the microcontroller during the design phase based on requirements, then generates firmware tailored to it. Code handles sensor reading, motor control, communication protocols, power management, and safety features. Templates are validated per microcontroller family and customized to the specific hardware in the design.

Firmware is pre-flashed to delivered hardware where applicable. Over-the-air update infrastructure allows users to receive improvements, bug fixes, and new features after delivery without ever opening the device.

### 5.7 Companion App Generation

For every project that needs user interaction, the agent generates a companion app from the Unified Runtime protocol described in 5.5. The app, the simulation, the keyboard mapping, and the firmware all derive from the same control schema, so behavior is identical across all of them.

The default delivery is a Progressive Web App accessible via a custom URL the user can share with anyone (e.g., cassen.ai/p/[project]/control). No installation required, works on any phone or computer. Users open the same URL during Test Room simulation and after receiving the physical product — the experience is seamless.

For more complex projects, a native mobile shell app houses each project as a card, allowing users to control multiple products from one place.

App generation covers virtual joysticks, sliders, buttons, toggles, sensor displays, camera feeds, and telemetry. Users describe what controls they want during the design phase and the agent builds the interface.

For users who prefer physical controls, the platform offers custom physical controller design — handheld units with screens, sticks, and buttons — generated as printable hardware that pairs with the project. These are sourced through the marketplace like any other custom component. Users can also connect any standard game controller (Xbox, PlayStation, Switch Pro, generic) and the Unified Runtime auto-maps the controller's inputs to the product's control schema through the Web Gamepad API.

Voice and smart-home integrations connect projects to Alexa, Google Home, and Siri. Cloud features support multi-device sync, scheduling, automation, and remote control.

### 5.8 Parts Marketplace

Users review the project's bill of materials with live pricing and click to order. The platform routes orders across multiple suppliers — Digikey, Mouser, LCSC, McMaster-Carr, JLCPCB, Misumi, Amazon Business, and others — and consolidates fulfillment.

Single checkout splits the BOM intelligently across vendors based on availability, price, and lead time. Users can choose consolidated shipping (single delivery) or direct from each supplier (faster).

Order tracking, returns, and replacements are managed through the platform's unified interface. Users never deal with multiple supplier accounts.

### 5.9 Custom Fabrication

For parts that don't exist off-the-shelf — enclosures, brackets, custom shells, frames, panels — the platform offers on-demand fabrication.

Available processes include 3D printing in plastic (FDM with PLA, PETG, ABS; SLA resin; MJF nylon), 3D printing in metal (SLM and DMLS in stainless, aluminum, and titanium), CNC milling, sheet metal cutting and bending, laser cutting, and injection molding for production runs.

Fabrication is routed to vetted partners — Xometry, Hubs, Fictiv, Shapeways, JLCPCB, PCBWay, SendCutSend, and others. The agent picks the right vendor based on material, finish, lead time, and budget.

Users without their own machines order through the platform. Users with their own 3D printers, CNC mills, or laser cutters can export clean STL, STEP, DXF, or G-code files for self-fabrication.

Quality is guaranteed through SLAs with fabrication partners. Reprints and replacements are handled by the platform.

### 5.10 On-Demand Assembled Prototypes

For users who want the finished product without assembling it themselves, the platform offers fully assembled, tested, and ready-to-use prototypes.

Assembly is done through partner facilities or in-house assembly operations. Each prototype undergoes quality control before shipping. Documentation, instructions, and warranty information are included.

### 5.11 Deep Research Mode

For users with serious commercial intent, deep research is a premium tier of investigation that goes substantially beyond standard research depth.

Multi-pass component sourcing evaluates dozens of alternatives per component across cost, lead time, MOQ, lifecycle status, and obsolescence risk. Datasheets are read in full and cross-referenced — including PDF parsing — to catch edge cases and incompatibilities standard research misses.

Failure mode and effects analysis (FMEA) walks through what could fail at each subsystem and proposes mitigations. Compliance and certification research covers FCC, CE, UL, RoHS, battery shipping regulations, and industry-specific standards.

Monte Carlo simulation runs hundreds of variations across temperature ranges, manufacturing tolerances, and edge case conditions. Design for manufacturing (DFM) review evaluates whether the design can be produced at scale.

Output is a long-form PDF engineering report suitable for sharing with co-founders, investors, or manufacturing partners.

### 5.12 Project Management & Collaboration

Projects are saved with full version history. Users can fork, branch, and revert designs.

Team collaboration supports multi-user workspaces with real-time editing, commenting, and review tools. Projects can be public (visible to the community) or private.

A template library provides starting points for common project types. Public projects are forkable, encouraging community-driven design sharing.

Knowledge packs and design data accumulate across the platform's user base, continuously improving the agent's recommendations and validation accuracy.

---

## 6. Technical Architecture

### 6.1 Reasoning Layer

LLM-powered multi-agent orchestration with knowledge pack system for domain expertise. Vector database grounds component selection in real, available parts. Live web search augments structured data for current pricing, availability, and emerging components.

### 6.2 Workshop Rendering Layer

Hybrid rendering pipeline targeting photorealism by default. Real-time interaction runs in the browser through WebGPU with physically-based rendering — real materials, real lighting, real shadows, real reflections. Three.js or Babylon.js as the runtime, React Three Fiber for declarative React integration. For pause-and-inspect moments and shareable hero shots, the platform invokes cloud-rendered ray tracing through NVIDIA Omniverse and streams full ray-traced output back to the browser as high-resolution images and video. The transition between interactive and photoreal is seamless to the user. WebXR for AR and VR viewing. Real-time collaboration through synchronized state.

### 6.3 Test Room Physics Layer

Cloud-based simulation infrastructure integrating NVIDIA Newton, MuJoCo Warp, Disney Research Kamino solver, PyBullet, ngspice for circuit simulation, OpenFOAM for batch CFD, and specialized solvers as needed. Tiered approach: real-time interactive simulation for live testing, high-accuracy batch simulation for deep research mode. Auto-configuration translates designs to runnable scenes from CAD metadata. Environmental control system manages wind, temperature, humidity, gravity, surface properties, and lighting.

### 6.4 Unified Runtime Layer

Single control protocol schema derived from project intent. Four parallel implementations: simulation runtime (in the Test Room), companion app runtime (PWA + native shell), input mapping runtime (keyboard, gamepad, custom controllers via Web Gamepad API), and firmware runtime (compiled to the target microcontroller). All four implementations share generated code paths and the same control schema, guaranteeing behavioral parity between simulation and real hardware.

### 6.5 Code Generation Layer

Firmware templates per microcontroller family. App framework based on React Native and PWA. Build pipeline emits all four runtime implementations from the single Unified Runtime schema. OTA update infrastructure for delivered devices.

### 6.6 Marketplace & Logistics Layer

Supplier API integrations for live data and order placement. Order routing engine with consolidation logic. Payment processing across geographies. Customer support tooling integrated with project context.

### 6.7 Data & Learning Layer

Simulation results dataset growing with every Test Room session. Project success and failure tracking. Continuous agent improvement through fine-tuning, retrieval enhancement, and validation feedback loops. The dataset becomes a structural moat over time.

---

## 7. Success Metrics

**Engagement metrics.** Projects created per active user per month, simulation runs per project, iterations per project before order, time from goal to first viable design.

**Quality metrics.** Order success rate (parts fit and work as designed), return rate, customer satisfaction (NPS), time from order to delivery, and assembled prototype success rate.

**Growth metrics.** Signup-to-active conversion, viral coefficient, organic versus paid acquisition mix, and geographic distribution of users.

---

## 8. Differentiation

The platform's defensibility compounds across several dimensions.

Cross-domain general-purpose capability has no direct competitor. Vertical players cover narrow slices. The platform covers the entire surface of physical product creation in one tool.

End-to-end stack from idea to assembled product means users don't switch tools mid-project. Every step lives on the platform, creating switching costs that grow with each project.

Physics-validated designs build user trust no static design tool can match. Watching a design work in simulation before ordering parts is fundamentally different from looking at a 3D render.

Software plus hardware integration is unique. No design tool generates firmware and apps. No firmware tool designs hardware. The combined offering creates a complete product where competitors offer fragments.

The simulation and design dataset becomes a structural moat. Every run improves the agent. Late entrants cannot replicate this without years of usage data.

Marketplace network effects strengthen both supply and demand sides. Both reinforce each other.

---

*End of document.*