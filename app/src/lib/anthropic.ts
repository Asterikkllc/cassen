import "server-only";
import Anthropic from "@anthropic-ai/sdk";

let _client: Anthropic | null = null;

/**
 * Server-side Anthropic client. Cached per process. Used by the
 * /api/chat route as a direct LLM call while we scaffold; the real
 * agent service (FastAPI + LangGraph) takes over in the next slice
 * via AGENT_BASE_URL.
 */
export function getAnthropic(): Anthropic {
  if (_client) return _client;
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) throw new Error("ANTHROPIC_API_KEY not configured");
  _client = new Anthropic({ apiKey: key, maxRetries: 4 });
  return _client;
}

/**
 * Default model for the chat surface. Sonnet 4.6 gives a sane
 * speed/quality tradeoff for a project-talk-back loop; Opus only
 * makes sense once the agent core is doing heavy tool use.
 */
export const CHAT_MODEL = "claude-sonnet-4-6";
