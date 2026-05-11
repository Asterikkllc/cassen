import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

/**
 * Routes that require a signed-in Clerk session. Everything under
 * `/projects/*` is the product surface; `/api/*` (except the public
 * sign-in/up flows) is server-only and needs auth.
 *
 * Public surface: `/`, `/sign-in`, `/sign-up`, and any static assets.
 *
 * Next 16 renamed the middleware convention to `proxy.ts`, but
 * Clerk's helper is still wired through `middleware.ts` — both file
 * names are accepted; landing/ also uses `middleware.ts` against
 * Next 16.2.4 successfully, so we follow that pattern here.
 */
const isProtectedRoute = createRouteMatcher([
  "/projects(.*)",
  "/api/chat(.*)",
  "/api/projects(.*)",
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next internals + every static asset by extension; run on
    // every page and API route.
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
