import "server-only";
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import {
  type CookieOptions,
  createServerClient as createServerClientWithCookies,
} from "@supabase/ssr";

export async function getSupabaseServer() {
  const cookieStore = await cookies();
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

  return createServerClient(url, anon, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const { name, value, options } of cookiesToSet) {
            cookieStore.set(name, value, options);
          }
        } catch {
          // Called from a Server Component — cookies can't be set there.
          // Middleware refreshes the session, so this is safe to ignore.
        }
      },
    },
  });
}

export type { CookieOptions };
export { createServerClientWithCookies };
