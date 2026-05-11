"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { ArrowUp, ChevronDown, Loader2, User, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";

export type ChatToolCall = {
  id?: string;
  name?: string;
  input?: unknown;
  output_text?: string;
  is_error?: boolean;
  error?: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  thinking?: string | null;
  toolCalls?: ChatToolCall[] | null | unknown;
  createdAt?: string;
  /** Stream-time only: token text accumulating before persistence completes. */
  streaming?: boolean;
};

export type ChatThreadProps = {
  projectId: string;
  initialMessages: ChatMessage[];
};

type SsePayload = {
  kind: "token" | "message-end" | "error";
  text?: string;
  error?: string;
};

function asToolCalls(value: unknown): ChatToolCall[] {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (v): v is ChatToolCall => !!v && typeof v === "object",
  );
}

/**
 * Chat surface for a project. Renders the persisted message thread
 * and an input bar that streams new assistant turns from `/api/chat`.
 * Tool calls (when the agent uses them in later slices) collapse into
 * a `<details>` Thinking disclosure under each bubble.
 */
export function ChatThread({ projectId, initialMessages }: ChatThreadProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const router = useRouter();

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    setError(null);
    const localUserId = `local-user-${Date.now()}`;
    const localAssistantId = `local-asst-${Date.now() + 1}`;
    setMessages((prev) => [
      ...prev,
      { id: localUserId, role: "user", content: text },
      {
        id: localAssistantId,
        role: "assistant",
        content: "",
        streaming: true,
      },
    ]);
    setInput("");
    setSending(true);

    let res: Response;
    try {
      res = await fetch(`/api/chat`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ projectId, message: text }),
      });
    } catch (err) {
      setSending(false);
      setError(`Network error: ${(err as Error).message}`);
      setMessages((prev) => prev.filter((m) => m.id !== localAssistantId));
      return;
    }

    if (!res.ok || !res.body) {
      setSending(false);
      setError(
        `Chat failed (${res.status}): ${(await res.text()).slice(0, 200)}`,
      );
      setMessages((prev) => prev.filter((m) => m.id !== localAssistantId));
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let assistantText = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let frameEnd = buffer.indexOf("\n\n");
        while (frameEnd !== -1) {
          const frame = buffer.slice(0, frameEnd);
          buffer = buffer.slice(frameEnd + 2);
          frameEnd = buffer.indexOf("\n\n");

          const dataLines = frame
            .split("\n")
            .filter((l) => l.startsWith("data:"))
            .map((l) => l.slice(5).trimStart());
          if (dataLines.length === 0) continue;

          let payload: SsePayload;
          try {
            payload = JSON.parse(dataLines.join("\n")) as SsePayload;
          } catch {
            continue;
          }

          if (payload.kind === "token" && payload.text) {
            assistantText += payload.text;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === localAssistantId
                  ? { ...m, content: assistantText }
                  : m,
              ),
            );
          } else if (payload.kind === "error") {
            setError(payload.error ?? "Unknown chat error");
          }
        }
      }
    } finally {
      setSending(false);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === localAssistantId ? { ...m, streaming: false } : m,
        ),
      );
      // Refresh the route so the sidebar's recents list picks up
      // any project status changes the conversation triggers.
      router.refresh();
    }
  }, [input, projectId, sending, router]);

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center px-4 text-center text-sm text-muted-foreground">
            Start a conversation with the agent.
          </div>
        ) : (
          <ol className="mx-auto flex max-w-3xl flex-col gap-6">
            {messages.map((m) => (
              <ChatMessageRow key={m.id} message={m} />
            ))}
          </ol>
        )}
      </div>

      {error ? (
        <div className="border-t border-destructive/40 bg-destructive/10 px-4 py-2 text-xs text-destructive">
          {error}
        </div>
      ) : null}

      <form
        className="border-t border-border bg-background/60 px-3 py-3 sm:px-6"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-border bg-card/80 px-3 py-2 focus-within:border-primary/40">
          <textarea
            className="max-h-48 min-h-9 flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-60"
            placeholder="Message the agent…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            rows={1}
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || input.trim().length === 0}
            className="grid h-8 w-8 place-items-center rounded-full bg-primary text-primary-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:bg-muted disabled:text-muted-foreground"
            aria-label="Send"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowUp className="h-4 w-4" />
            )}
          </button>
        </div>
        <p className="mx-auto mt-2 max-w-3xl text-center text-[10px] text-muted-foreground">
          Enter to send · Shift+Enter for newline
        </p>
      </form>
    </div>
  );
}

function ChatMessageRow({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const toolCalls = useMemo(() => asToolCalls(message.toolCalls), [
    message.toolCalls,
  ]);
  const hasThinking =
    Boolean(message.thinking && message.thinking.trim()) || toolCalls.length > 0;

  if (isSystem) {
    return (
      <li className="flex items-center justify-center gap-2 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
        <span className="h-px flex-1 bg-border" />
        <span>{message.content}</span>
        <span className="h-px flex-1 bg-border" />
      </li>
    );
  }

  return (
    <li className={cn("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser ? (
        <div className="grid h-7 w-7 flex-shrink-0 place-items-center rounded-full bg-primary/15 font-mono text-[9px] font-semibold text-primary">
          CA
        </div>
      ) : null}
      <div
        className={cn(
          "flex max-w-[85%] flex-col gap-2",
          isUser ? "items-end" : "items-start",
        )}
      >
        <div
          className={cn(
            "whitespace-pre-wrap break-words rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-card text-foreground",
          )}
        >
          {message.content}
          {message.streaming && message.content.length === 0 ? (
            <span className="inline-flex items-center gap-1 text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span className="text-xs">thinking</span>
            </span>
          ) : null}
          {message.streaming && message.content.length > 0 ? (
            <span className="ml-1 inline-block h-3 w-1.5 animate-pulse bg-primary/60" />
          ) : null}
        </div>

        {hasThinking ? (
          <details className="group w-full max-w-full rounded-md border border-border bg-card/40 text-xs text-muted-foreground">
            <summary className="flex cursor-pointer list-none items-center gap-1.5 px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wider hover:text-foreground">
              <ChevronDown className="h-3 w-3 transition-transform group-open:rotate-180" />
              Thinking
              {toolCalls.length > 0 ? (
                <span className="rounded bg-muted px-1.5 text-[9px]">
                  {toolCalls.length} tool call{toolCalls.length === 1 ? "" : "s"}
                </span>
              ) : null}
            </summary>
            <div className="space-y-3 border-t border-border px-3 py-2">
              {message.thinking ? (
                <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-muted-foreground">
                  {message.thinking}
                </pre>
              ) : null}
              {toolCalls.map((tc, i) => (
                <div
                  key={tc.id ?? i}
                  className={cn(
                    "rounded border bg-background/60 px-2.5 py-1.5",
                    tc.is_error || tc.error
                      ? "border-destructive/40"
                      : "border-border",
                  )}
                >
                  <div className="flex items-center gap-1.5 font-mono text-[10px]">
                    <Wrench className="h-3 w-3" />
                    <span className="text-primary">{tc.name ?? "tool"}</span>
                  </div>
                </div>
              ))}
            </div>
          </details>
        ) : null}
      </div>
      {isUser ? (
        <div className="grid h-7 w-7 flex-shrink-0 place-items-center rounded-full bg-muted">
          <User className="h-3.5 w-3.5 text-muted-foreground" />
        </div>
      ) : null}
    </li>
  );
}
