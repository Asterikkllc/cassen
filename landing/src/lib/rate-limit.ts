import "server-only";
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const UPSTASH_URL = process.env.UPSTASH_REDIS_REST_URL;
const UPSTASH_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;

type LimiterDef = {
  limit: number;
  windowSeconds: number;
};

const limiterCache = new Map<string, Ratelimit>();

function getUpstashLimiter(name: string, def: LimiterDef): Ratelimit | null {
  if (!UPSTASH_URL || !UPSTASH_TOKEN) return null;
  const cached = limiterCache.get(name);
  if (cached) return cached;
  const limiter = new Ratelimit({
    redis: new Redis({ url: UPSTASH_URL, token: UPSTASH_TOKEN }),
    limiter: Ratelimit.slidingWindow(def.limit, `${def.windowSeconds} s`),
    analytics: true,
    prefix: `cassen:rl:${name}`,
  });
  limiterCache.set(name, limiter);
  return limiter;
}

type MemEntry = { hits: number[] };
const memBuckets = new Map<string, MemEntry>();
let warnedMissingUpstash = false;

function memoryRateCheck(
  key: string,
  def: LimiterDef,
  now: number,
): RateCheck {
  if (!warnedMissingUpstash) {
    warnedMissingUpstash = true;
    console.warn(
      "[rate-limit] UPSTASH_REDIS_REST_URL / _TOKEN not set — using in-memory limiter. NOT PRODUCTION-SAFE: provision Upstash Redis before deploying.",
    );
  }
  const windowMs = def.windowSeconds * 1000;
  const entry = memBuckets.get(key) ?? { hits: [] };
  const cutoff = now - windowMs;
  entry.hits = entry.hits.filter((t) => t > cutoff);
  if (entry.hits.length >= def.limit) {
    const oldest = entry.hits[0];
    return {
      ok: false,
      remaining: 0,
      retryAfterMs: Math.max(0, windowMs - (now - oldest)),
    };
  }
  entry.hits.push(now);
  memBuckets.set(key, entry);
  return { ok: true, remaining: def.limit - entry.hits.length, retryAfterMs: 0 };
}

export type RateCheck = {
  ok: boolean;
  remaining: number;
  retryAfterMs: number;
};

export const RATE_LIMITS = {
  signup_ip: { limit: 5, windowSeconds: 60 * 60 },
  admin_login_ip: { limit: 10, windowSeconds: 60 * 60 },
} satisfies Record<string, LimiterDef>;

export type LimiterName = keyof typeof RATE_LIMITS;

export async function checkRateLimit(
  name: LimiterName,
  identifier: string,
): Promise<RateCheck> {
  const def = RATE_LIMITS[name];
  const upstash = getUpstashLimiter(name, def);
  if (upstash) {
    const res = await upstash.limit(identifier);
    return {
      ok: res.success,
      remaining: res.remaining,
      retryAfterMs: Math.max(0, res.reset - Date.now()),
    };
  }
  return memoryRateCheck(`${name}:${identifier}`, def, Date.now());
}

export function getClientIp(headers: Headers): string {
  const xff = headers.get("x-forwarded-for");
  if (xff) {
    const first = xff.split(",")[0]?.trim();
    if (first) return first;
  }
  return (
    headers.get("x-real-ip") ??
    headers.get("cf-connecting-ip") ??
    headers.get("x-vercel-forwarded-for") ??
    "unknown"
  );
}
