import Link from "next/link";
import { redirect } from "next/navigation";
import { auth } from "@clerk/nextjs/server";
import { ArrowRight } from "lucide-react";

export const dynamic = "force-dynamic";

/**
 * Root entry. Signed-in users go straight to the product (their
 * project list); signed-out users see a brief value-prop + sign-in
 * link. The dedicated marketing site lives at `landing/` and is
 * deployed separately on the apex domain.
 */
export default async function RootPage() {
  const { userId } = await auth();
  if (userId) {
    redirect("/projects");
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-6 py-16 text-center">
      <div className="flex flex-col items-center gap-6">
        <span className="grid h-12 w-12 place-items-center rounded-xl bg-primary/10 font-mono text-sm font-semibold text-primary">
          CA
        </span>
        <h1 className="text-balance text-4xl font-semibold tracking-tight md:text-5xl">
          Describe a physical product.
          <br />
          <span className="text-primary">Cassen builds it.</span>
        </h1>
        <p className="max-w-xl text-pretty text-base text-muted-foreground md:text-lg">
          Design, simulate, source, fabricate, and ship — all from one chat.
          Bring an idea; receive a working result.
        </p>
        <div className="mt-4 flex flex-col items-center gap-3 sm:flex-row">
          <Link
            href="/sign-in"
            className="inline-flex h-11 items-center justify-center rounded-full bg-primary px-6 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
          >
            Sign in
            <ArrowRight className="ml-1.5 h-4 w-4" />
          </Link>
          <Link
            href="/sign-up"
            className="inline-flex h-11 items-center justify-center rounded-full border border-border px-6 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Create an account
          </Link>
        </div>
      </div>
    </main>
  );
}
