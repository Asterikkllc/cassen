import { auth, currentUser } from "@clerk/nextjs/server";
import { SiteHeader } from "@/components/site-header";
import { listMyProjects } from "@/app/actions/projects";

export const metadata = { title: "Projects" };
export const dynamic = "force-dynamic";

const STATUS_LABEL: Record<string, string> = {
  draft: "Draft",
  planning: "Planning",
  designing: "Designing",
  simulating: "Simulating",
  sourcing: "Sourcing",
  fabricating: "Fabricating",
  assembled: "Assembled",
  shipped: "Shipped",
  archived: "Archived",
  failed: "Failed",
};

export default async function ProjectsPage() {
  await auth.protect();
  const user = await currentUser();
  const greeting =
    user?.firstName ?? user?.username ?? user?.emailAddresses[0]?.emailAddress;

  const projects = await listMyProjects();

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
            {projects.length === 0
              ? "You don't have any projects yet."
              : `You have ${projects.length} project${projects.length === 1 ? "" : "s"}.`}
          </p>
        </div>

        {projects.length === 0 ? (
          <div className="mt-12 rounded-2xl border border-dashed border-neutral-800 bg-neutral-900/30 p-10 text-center">
            <p className="text-sm text-neutral-400">
              The new-project flow ships in the next phase. The data layer is
              wired — once you describe a product, it&apos;ll land here.
            </p>
          </div>
        ) : (
          <ul className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2">
            {projects.map((p) => (
              <li
                key={p.id}
                className="rounded-2xl border border-neutral-800 bg-neutral-900/40 p-5"
              >
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-base font-medium text-white">
                    {p.title ?? "Untitled project"}
                  </h2>
                  <span className="shrink-0 rounded-full border border-neutral-800 bg-neutral-900 px-2.5 py-0.5 text-xs text-neutral-400">
                    {STATUS_LABEL[p.status] ?? p.status}
                  </span>
                </div>
                <p className="mt-3 line-clamp-3 text-sm text-neutral-400">
                  {p.prompt}
                </p>
                <p className="mt-4 text-xs text-neutral-600">
                  Created {new Date(p.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ul>
        )}
      </main>
    </>
  );
}
