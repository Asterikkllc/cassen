import { auth, currentUser } from "@clerk/nextjs/server";
import { SiteHeader } from "@/components/site-header";

export const metadata = { title: "Projects" };

export default async function ProjectsPage() {
  await auth.protect();
  const user = await currentUser();
  const greeting =
    user?.firstName ?? user?.username ?? user?.emailAddresses[0]?.emailAddress;

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-5xl px-6 py-16">
        <div className="flex flex-col gap-3">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-500">
            Projects
          </p>
          <h1 className="text-balance text-3xl font-semibold tracking-tight text-white md:text-4xl">
            {greeting ? `Welcome, ${greeting}.` : "Welcome."}
          </h1>
          <p className="text-pretty text-neutral-400">
            You don&apos;t have any projects yet. Soon, this is where you&apos;ll
            describe a product and watch the agent design it.
          </p>
        </div>

        <div className="mt-12 rounded-2xl border border-dashed border-neutral-800 bg-neutral-900/30 p-10 text-center">
          <p className="text-sm text-neutral-400">
            The new-project flow ships in a later phase. Until then, this page
            confirms you&apos;re authenticated and the protected routing works.
          </p>
        </div>
      </main>
    </>
  );
}
