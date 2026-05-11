import { NextResponse, type NextRequest } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { z } from "zod";
import { CHAT_MODEL, getAnthropic } from "@/lib/anthropic";
import { getSupabaseAdmin } from "@/lib/supabase";
import { getMyProject } from "@/app/actions/projects";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BodySchema = z.object({
  projectId: z.string().min(1),
  message: z.string().trim().min(1).max(8000),
});

const SYSTEM_PROMPT = `You are the Cassen design agent in conversation mode.

The user is on cassen.ai — they described a physical product they want built. Cassen is a general-purpose agent that designs, simulates, sources, fabricates, and ships physical products. The user's current project lives in this chat thread.

Slice-0 scope: you're the FRONT of the agent. You acknowledge the user's project, ask 1-2 focused clarifying questions if needed, and tell them when you're about to dispatch the design pipeline. The full pipeline (knowledge-pack research, Workshop CAD assembly, Test Room physics, BoM generation) is a separate service that lands in the next slice — for now you're scoped to conversation only.

Tone: professional engineer, not chatbot. Replies are typically 1-4 sentences. Make reasonable assumptions; don't stall waiting for the user to specify every detail.

Materials: when the user is describing a project, treat their first message as a complete-enough brief unless something critical is missing. One question max before acknowledging the brief is good. Don't overwhelm with a list of questions.`;

// SSE frame helper. The chat-thread client parses these as
// `{ kind: "token" | "message-end" | "error" }`.
function sse(payload: Record<string, unknown>): string {
  return `data: ${JSON.stringify(payload)}\n\n`;
}

/**
 * POST /api/chat
 *
 * Body: `{ projectId, message }`.
 *
 * Persists the user's message → streams an assistant reply via SSE →
 * persists the full assistant reply when streaming completes. This is
 * Slice 0's stand-in for the future LangGraph agent service — once
 * AGENT_BASE_URL is configured, this route will forward to it instead
 * of calling Anthropic directly.
 */
export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let parsed: z.infer<typeof BodySchema>;
  try {
    parsed = BodySchema.parse(await req.json());
  } catch (err) {
    return NextResponse.json(
      { error: `Invalid body: ${(err as Error).message}` },
      { status: 400 },
    );
  }

  const project = await getMyProject(parsed.projectId);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }

  // If AGENT_BASE_URL is set, proxy to the agent service. The agent
  // persists the user + assistant messages itself, so we skip the
  // direct-DB insert below in that case. Direct-Anthropic fallback
  // still runs when the agent isn't deployed (early development).
  const agentBase = (process.env.AGENT_BASE_URL || "").trim();
  if (agentBase) {
    const upstream = await fetch(`${agentBase.replace(/\/$/, "")}/runs/chat-stream`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "text/event-stream",
        ...(process.env.AGENT_SHARED_SECRET
          ? { authorization: `Bearer ${process.env.AGENT_SHARED_SECRET}` }
          : {}),
      },
      body: JSON.stringify({
        project_id: project.id,
        message: parsed.message,
      }),
      cache: "no-store",
    }).catch((err) => {
      console.error("[chat] agent fetch failed", err);
      return null;
    });
    if (upstream && upstream.ok && upstream.body) {
      return new Response(upstream.body, {
        status: 200,
        headers: {
          "content-type": "text/event-stream",
          "cache-control": "no-cache, no-transform",
          connection: "keep-alive",
          "x-accel-buffering": "no",
        },
      });
    }
    // Agent unreachable or rejected — fall through to direct
    // Anthropic so the user still gets a reply.
    console.warn(
      "[chat] agent upstream unhealthy; falling back to direct Anthropic",
      upstream?.status,
    );
  }

  const admin = getSupabaseAdmin();

  // 1. Persist user message immediately. SSE consumers see it on a
  //    refresh even if the stream drops.
  await admin.from("project_messages").insert({
    project_id: project.id,
    role: "user",
    content: parsed.message,
  });

  // 2. Build the Anthropic message array from the persisted thread
  //    (oldest-first), filtered to user/assistant only. System
  //    messages exist for UI dividers, not for Claude context.
  const { data: history } = await admin
    .from("project_messages")
    .select("role, content")
    .eq("project_id", project.id)
    .order("created_at", { ascending: true })
    .limit(50);
  const apiMessages = (history ?? [])
    .filter((m) => m.role === "user" || m.role === "assistant")
    .map((m) => ({
      role: m.role as "user" | "assistant",
      content: typeof m.content === "string" ? m.content : "",
    }))
    .filter((m) => m.content.length > 0);

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const encoder = new TextEncoder();
      const textParts: string[] = [];

      try {
        const client = getAnthropic();
        const result = await client.messages.stream({
          model: CHAT_MODEL,
          max_tokens: 1024,
          system: SYSTEM_PROMPT,
          messages: apiMessages,
        });
        for await (const event of result) {
          if (
            event.type === "content_block_delta" &&
            event.delta.type === "text_delta"
          ) {
            const text = event.delta.text;
            if (text) {
              textParts.push(text);
              controller.enqueue(encoder.encode(sse({ kind: "token", text })));
            }
          }
        }
      } catch (err) {
        const msg = (err as Error).message ?? "unknown chat error";
        controller.enqueue(encoder.encode(sse({ kind: "error", error: msg })));
      }

      const fullText = textParts.join("").trim();
      if (fullText) {
        await admin.from("project_messages").insert({
          project_id: project.id,
          role: "assistant",
          content: fullText,
        });
      }
      controller.enqueue(
        encoder.encode(sse({ kind: "message-end", text: fullText })),
      );
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache, no-transform",
      connection: "keep-alive",
      "x-accel-buffering": "no",
    },
  });
}
