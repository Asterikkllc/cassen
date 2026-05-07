"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Loader2,
  Play,
  Sparkles,
  Wrench,
} from "lucide-react";
import { Button } from "@/components/ui/button";

type ToolCall = {
  id: string;
  name: string;
  input?: unknown;
  output_text?: string;
  is_error?: boolean;
  error?: string;
  status: "running" | "done" | "error";
};

type RunEvent =
  | { kind: "status"; node?: string | null; data: { status: string } }
  | { kind: "node-start"; node: string; data: null }
  | { kind: "token"; node: string; data: string }
  | {
      kind: "node-end";
      node: string;
      data: { text?: string; parsed?: unknown; candidate_parts?: unknown[]; calls_made?: number };
    }
  | { kind: "iteration"; node: string; data: { i: number } }
  | {
      kind: "tool-call-start";
      node: string;
      data: { id: string; name: string; input: unknown };
    }
  | {
      kind: "tool-call-end";
      node: string;
      data: { id: string; name: string; output_text: string; is_error: boolean };
    }
  | {
      kind: "tool-error";
      node: string;
      data: { id?: string; name?: string; error: string };
    }
  | { kind: "complete"; node?: string | null; data: { status: string } }
  | { kind: "error"; node?: string | null; data: { message: string } };

type NodeBuffer = {
  node: string;
  text: string;
  toolCalls: ToolCall[];
  done: boolean;
};

type Status = "idle" | "running" | "done" | "error";

const NODE_LABEL: Record<string, string> = {
  planner: "Planning",
  electronics_research: "Researching electronics",
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
          return [
            ...prev,
            mutate({ node: nodeId, text: "", toolCalls: [], done: false }),
          ];
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
          updateNode(ev.node, () => ({
            node: ev.node,
            text: "",
            toolCalls: [],
            done: false,
          }));
          break;
        case "token":
          updateNode(ev.node, (b) => ({ ...b, text: b.text + ev.data }));
          break;
        case "node-end":
          updateNode(ev.node, (b) => ({
            ...b,
            text: ev.data.text ?? b.text,
            done: true,
          }));
          break;
        case "tool-call-start":
          updateNode(ev.node, (b) => ({
            ...b,
            toolCalls: [
              ...b.toolCalls,
              {
                id: ev.data.id,
                name: ev.data.name,
                input: ev.data.input,
                status: "running",
              },
            ],
          }));
          break;
        case "tool-call-end":
          updateNode(ev.node, (b) => ({
            ...b,
            toolCalls: b.toolCalls.map((c) =>
              c.id === ev.data.id
                ? {
                    ...c,
                    output_text: ev.data.output_text,
                    is_error: ev.data.is_error,
                    status: ev.data.is_error ? "error" : "done",
                  }
                : c,
            ),
          }));
          break;
        case "tool-error":
          updateNode(ev.node, (b) => {
            const id = ev.data.id;
            if (id) {
              return {
                ...b,
                toolCalls: b.toolCalls.map((c) =>
                  c.id === id
                    ? { ...c, error: ev.data.error, status: "error" }
                    : c,
                ),
              };
            }
            return {
              ...b,
              toolCalls: [
                ...b.toolCalls,
                {
                  id: `err-${b.toolCalls.length}`,
                  name: ev.data.name ?? "tool",
                  error: ev.data.error,
                  status: "error",
                },
              ],
            };
          });
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
            /* ignore malformed */
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
          agent decompose the prompt, ground electronic components in real
          parts, and sketch a first-pass design.
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

          {n.toolCalls.length > 0 ? (
            <div className="mb-4 flex flex-col gap-2">
              {n.toolCalls.map((c) => (
                <ToolCallRow key={c.id} call={c} />
              ))}
            </div>
          ) : null}

          {n.text ? (
            <pre className="whitespace-pre-wrap break-words font-sans text-sm leading-relaxed text-neutral-200">
              {n.text}
            </pre>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function ToolCallRow({ call }: { call: ToolCall }) {
  const [open, setOpen] = useState(false);
  const inputSummary = call.input
    ? truncate(JSON.stringify(call.input), 80)
    : "";
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900/40 text-xs">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 text-neutral-500" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-neutral-500" />
        )}
        {call.status === "error" ? (
          <AlertCircle className="h-3.5 w-3.5 text-red-400" />
        ) : (
          <Wrench
            className={
              call.status === "running"
                ? "h-3.5 w-3.5 animate-pulse text-emerald-400"
                : "h-3.5 w-3.5 text-emerald-400"
            }
          />
        )}
        <span className="font-mono text-neutral-200">{call.name}</span>
        {inputSummary ? (
          <span className="truncate text-neutral-500">({inputSummary})</span>
        ) : null}
        <span className="ml-auto text-neutral-500">
          {call.status === "running"
            ? "running"
            : call.status === "error"
              ? "error"
              : "done"}
        </span>
      </button>
      {open ? (
        <div className="border-t border-neutral-800 px-3 py-2">
          {call.input ? (
            <>
              <p className="text-neutral-500">input</p>
              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-neutral-300">
                {JSON.stringify(call.input, null, 2)}
              </pre>
            </>
          ) : null}
          {call.error ? (
            <>
              <p className="mt-2 text-neutral-500">error</p>
              <pre className="mt-1 whitespace-pre-wrap text-red-300">
                {call.error}
              </pre>
            </>
          ) : null}
          {call.output_text ? (
            <>
              <p className="mt-2 text-neutral-500">output</p>
              <pre className="mt-1 max-h-64 overflow-auto whitespace-pre-wrap text-neutral-300">
                {call.output_text}
              </pre>
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function truncate(s: string, n: number) {
  return s.length <= n ? s : s.slice(0, n - 1) + "…";
}
