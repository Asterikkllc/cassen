import "server-only";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let _admin: SupabaseClient | null = null;

/**
 * Service-role Supabase client for server-side code. Bypasses RLS;
 * NEVER ship to the browser or to a server action that runs based
 * on unauthenticated input. Auth check (Clerk) MUST come first; this
 * client trusts whoever asks.
 *
 * Cached per process because `createClient` does some setup work and
 * the call is hot (every server action, every route).
 */
export function getSupabaseAdmin(): SupabaseClient {
  if (_admin) return _admin;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) {
    throw new Error(
      "Supabase env missing — set NEXT_PUBLIC_SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY",
    );
  }
  _admin = createClient(url, key, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
  return _admin;
}
