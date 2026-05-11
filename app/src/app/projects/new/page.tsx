import { NewProjectForm } from "@/components/new-project-form";

export const metadata = { title: "New project" };
export const dynamic = "force-dynamic";

export default function NewProjectPage() {
  return (
    <div className="h-full overflow-y-auto">
      <NewProjectForm />
    </div>
  );
}
