import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { auth } from "@clerk/nextjs/server";
import { SiteHeader } from "@/components/site-header";
import { NewProjectForm } from "@/components/new-project-form";

export const metadata = { title: "New project" };
export const dynamic = "force-dynamic";

export default async function NewProjectPage() {
  await auth.protect();

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl px-6 py-12">
        <Link
          href="/projects"
          className="inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          All projects
        </Link>

        <div className="mt-8 flex flex-col gap-3">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-500">
            New project
          </p>
          <h1 className="text-balance text-3xl font-semibold tracking-tight text-white md:text-4xl">
            Describe what you want to build.
          </h1>
          <p className="text-pretty text-neutral-400">
            One paragraph is plenty. The agent will ask follow-ups only if it
            actually needs them.
          </p>
        </div>

        <div className="mt-10">
          <NewProjectForm />
        </div>
      </main>
    </>
  );
}
