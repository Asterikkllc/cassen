#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { writeFile, mkdir } from "node:fs/promises";
import { dirname, isAbsolute, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";

const POLLINATIONS_BASE = "https://image.pollinations.ai/prompt";
const DEFAULT_MODEL = "flux";
const DEFAULT_WIDTH = 1024;
const DEFAULT_HEIGHT = 1024;
const FETCH_TIMEOUT_MS = 120_000;
const MAX_RETRIES = 2;

function buildUrl({ prompt, width, height, model, seed, nologo, enhance }) {
  const url = new URL(`${POLLINATIONS_BASE}/${encodeURIComponent(prompt)}`);
  url.searchParams.set("width", String(width));
  url.searchParams.set("height", String(height));
  url.searchParams.set("model", model);
  if (typeof seed === "number") url.searchParams.set("seed", String(seed));
  if (nologo !== false) url.searchParams.set("nologo", "true");
  if (enhance) url.searchParams.set("enhance", "true");
  return url.toString();
}

async function fetchImage(url) {
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const res = await fetch(url, {
        signal: controller.signal,
        headers: { Accept: "image/*" },
      });
      clearTimeout(timeout);
      if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`Pollinations responded ${res.status}: ${body.slice(0, 200)}`);
      }
      const buf = Buffer.from(await res.arrayBuffer());
      if (buf.length < 256) {
        throw new Error("Pollinations returned suspiciously small payload");
      }
      return buf;
    } catch (err) {
      clearTimeout(timeout);
      if (attempt === MAX_RETRIES) throw err;
      await delay(1500 * (attempt + 1));
    }
  }
  throw new Error("unreachable");
}

function resolveOutputPath(p) {
  const abs = isAbsolute(p) ? p : resolve(process.cwd(), p);
  return abs;
}

const server = new Server(
  { name: "cassen-image-gen", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "generate_image",
      description:
        "Generate an image from a text prompt using Pollinations.ai (Flux by default) and save it as a PNG file. Use detailed prompts for realistic 3D / photoreal results — describe lighting, materials, camera, and style.",
      inputSchema: {
        type: "object",
        properties: {
          prompt: {
            type: "string",
            description: "Detailed image prompt. Be specific about subject, materials, lighting, camera, and style.",
          },
          output_path: {
            type: "string",
            description: "Absolute or cwd-relative file path to save the PNG. Parent dirs are created if missing.",
          },
          width: {
            type: "integer",
            default: DEFAULT_WIDTH,
            minimum: 256,
            maximum: 2048,
          },
          height: {
            type: "integer",
            default: DEFAULT_HEIGHT,
            minimum: 256,
            maximum: 2048,
          },
          model: {
            type: "string",
            default: DEFAULT_MODEL,
            description: "Pollinations model — flux (default, best quality), turbo (fast), or any other supported model id.",
          },
          seed: {
            type: "integer",
            description: "Optional seed for reproducible generations.",
          },
          enhance: {
            type: "boolean",
            description: "Have Pollinations rewrite the prompt for better quality.",
            default: false,
          },
        },
        required: ["prompt", "output_path"],
        additionalProperties: false,
      },
    },
    {
      name: "build_image_url",
      description:
        "Return the Pollinations URL for a given prompt without downloading. Useful when the caller wants to embed the URL or fetch later.",
      inputSchema: {
        type: "object",
        properties: {
          prompt: { type: "string" },
          width: { type: "integer", default: DEFAULT_WIDTH },
          height: { type: "integer", default: DEFAULT_HEIGHT },
          model: { type: "string", default: DEFAULT_MODEL },
          seed: { type: "integer" },
          enhance: { type: "boolean", default: false },
        },
        required: ["prompt"],
        additionalProperties: false,
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args = {} } = req.params;

  if (name === "generate_image") {
    const {
      prompt,
      output_path,
      width = DEFAULT_WIDTH,
      height = DEFAULT_HEIGHT,
      model = DEFAULT_MODEL,
      seed,
      enhance = false,
    } = args;

    if (!prompt || !output_path) {
      throw new Error("`prompt` and `output_path` are required.");
    }

    const url = buildUrl({ prompt, width, height, model, seed, enhance });
    const buf = await fetchImage(url);
    const abs = resolveOutputPath(output_path);
    await mkdir(dirname(abs), { recursive: true });
    await writeFile(abs, buf);

    return {
      content: [
        {
          type: "text",
          text:
            `Saved ${buf.length.toLocaleString()} bytes to ${abs}\n` +
            `Source URL: ${url}`,
        },
      ],
    };
  }

  if (name === "build_image_url") {
    const {
      prompt,
      width = DEFAULT_WIDTH,
      height = DEFAULT_HEIGHT,
      model = DEFAULT_MODEL,
      seed,
      enhance = false,
    } = args;
    if (!prompt) throw new Error("`prompt` is required.");
    const url = buildUrl({ prompt, width, height, model, seed, enhance });
    return { content: [{ type: "text", text: url }] };
  }

  throw new Error(`Unknown tool: ${name}`);
});

const transport = new StdioServerTransport();
await server.connect(transport);
