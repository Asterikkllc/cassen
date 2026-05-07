"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Play, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";

type RunEvent =
  | { kind: "status"; node?: string | null; data: { status: string } }
  | { kind: "node-start"; node: string; data: null }
  | { kind: "token"; node: string; data: string }
  | {
      kind: "node-end";
      node: string;
      data: { text: string; parsed?: unknown };
    }
  | { kind: "complete"; node?: string | null; data: { status: string } }
  | { kind: "error"; node?: string | null; data: { message: string } };

type NodeBuffer = {
  node: string;
  text: string;
  done: boolean;
};

type Status = "idle" | "running" | "done" | "error";

const NODE_LABEL: Record<string, string> = {
  planner: "Planning",
  designer: "Designing",
};

export function AgentRun({ projectId }: { projectId: string }) {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes] = useState<NodeBuffer[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const updateNode = useCallback(
    (nodeId: string, mutate: (b: NodeBuffer) => NodeBuffer) => {
      setNodes((prev) => {
        const idx = prev.findIndex((n) => n.node === nodeId);
        if (idx === -1) {
          return [...prev, mutate({ node: nodeId, text: "", done: false })];
        }
        const next = prev.slice();
        next[idx] = mutate(next[idx]);
        return next;
      });
    },
    [],
  );

  const handleEvent = useCallback(
    (ev: RunEvent) => {
      switch (ev.kind) {
        case "node-start":
          updateNode(ev.node!, (b) => ({ ...b, text: "", done: false }));
          break;
        case "token":
          updateNode(ev.node, (b) => ({ ...b, text: b.text + ev.data }));
          break;
        case "node-end":
          updateNode(ev.node, (b) => ({
            ...b,
            text: ev.data.text,
            done: true,
          }));
          break;
        case "complete":
          setStatus("done");
          break;
        case "error":
          setStatus("error");
          setError(ev.data.message);
          break;
      }
    },
    [updateNode],
  );

  const start = useCallback(async () => {
    setStatus("running");
    setError(null);
    setNodes([]);
    const ctrl = new AbortController();
    abortRef.current?.abort();
    abortRef.current = ctrl;

    try {
      const res = await fetch(`/api/agent/runs/${projectId}/stream`, {
        method: "POST",
        signal: ctrl.signal,
      });
      if (!res.ok || !res.body) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error ?? `Agent error (HTTP ${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";
        for (const part of parts) {
          const dataLine = part
            .split("\n")
            .find((l) => l.startsWith("data:"));
          if (!dataLine) continue;
          try {
            handleEvent(JSON.parse(dataLine.slice(5).trim()) as RunEvent);
          } catch {
            // ignore malformed
          }
        }
      }
      setStatus((s) => (s === "running" ? "done" : s));
    } catch (err: unknown) {
      if ((err as Error)?.name === "AbortError") return;
      setStatus("error");
      setError((err as Error)?.message ?? "Run failed");
    }
  }, [handleEvent, projectId]);

  useEffect(() => () => abortRef.current?.abort(), []);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm text-neutral-400">
          <Sparkles className="h-4 w-4 text-emerald-400" />
          {status === "idle" && <span>Ready to start the agent.</span>}
          {status === "running" && (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Agent running…
            </span>
          )}
          {status === "done" && <span>Done.</span>}
          {status === "error" && (
            <span className="text-red-400">{error ?? "Failed."}</span>
          )}
        </div>
        <Button
          onClick={start}
          disabled={status === "running"}
          className="h-9 rounded-full bg-white px-4 text-sm font-medium text-neutral-950 hover:bg-neutral-200 disabled:opacity-60"
        >
          {status === "idle" && (
            <>
              <Play className="mr-1.5 h-4 w-4" /> Run agent
            </>
          )}
          {status === "running" && (
            <>
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Running
            </>
          )}
          {status === "done" && (
            <>
              <Play className="mr-1.5 h-4 w-4" /> Run again
            </>
          )}
          {status === "error" && (
            <>
              <Play className="mr-1.5 h-4 w-4" /> Retry
            </>
          )}
        </Button>
      </div>

      {nodes.length === 0 && status === "idle" ? (
        <p className="text-sm text-neutral-500">
          Hit <span className="text-neutral-300">Run agent</span> to have the
          agent decompose the prompt and sketch a first-pass design.
        </p>
      ) : null}

      {nodes.map((n) => (
        <article
          key={n.node}
          className="rounded-xl border border-neutral-800 bg-neutral-950/60 p-5"
        >
          <header className="mb-3 flex items-center justify-between text-xs uppercase tracking-wider text-neutral-500">
            <span>{NODE_LABEL[n.node] ?? n.node}</span>
            <span className="flex items-center gap-1.5">
              {n.done ? (
                <span className="text-emerald-400">complete</span>
              ) : (
                <>
                  <Loader2 className="h-3 w-3 animate-spin" />
                  streaming
                </>
              )}
            </span>
          </header>
          <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-neutral-200">
            {n.text}
          </pre>
        </article>
      ))}
    </div>
  );
}
