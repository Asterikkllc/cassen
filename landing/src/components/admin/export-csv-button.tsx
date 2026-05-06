import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ExportCsvButton() {
  return (
    <a
      href="/admin/export"
      className={cn(
        buttonVariants({ variant: "outline" }),
        "h-9 px-4 border-neutral-800 bg-neutral-900/50 text-neutral-100 hover:bg-neutral-800 hover:text-white",
      )}
    >
      Export CSV
    </a>
  );
}
