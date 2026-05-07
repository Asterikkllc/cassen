import { NextResponse, type NextRequest } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { getMyProject } from "@/app/actions/projects";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type Params = Promise<{ id: string }>;

export async function POST(_req: NextRequest, { params }: { params: Params }) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const { id } = await params;
  const project = await getMyProject(id);
  if (!project) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const base = process.env.AGENT_BASE_URL;
  const secret = process.env.AGENT_SHARED_SECRET;
  if (!base || !secret) {
    return NextResponse.json(
      { error: "Agent service not configured" },
      { status: 503 },
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${base.replace(/\/$/, "")}/runs/stream`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        accept: "text/event-stream",
        authorization: `Bearer ${secret}`,
      },
      body: JSON.stringify({
        project_id: project.id,
        owner_id: userId,
        prompt: project.prompt,
      }),
      cache: "no-store",
    });
  } catch (err) {
    console.error("[agent-proxy] upstream fetch failed", err);
    return NextResponse.json(
      { error: "Agent service unreachable" },
      { status: 502 },
    );
  }

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "");
    console.error("[agent-proxy] upstream error", upstream.status, text);
    return NextResponse.json(
      { error: "Agent service rejected the run" },
      { status: 502 },
    );
  }

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
