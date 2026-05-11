"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState, useTransition } from "react";
import {
  ChevronsLeft,
  ChevronsRight,
  MessageSquarePlus,
  PanelLeft,
  Search,
} from "lucide-react";
import { UserButton } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
import type { Project } from "@/lib/projects";

export type SidebarProject = Pick<
  Project,
  "id" | "title" | "prompt" | "status" | "created_at"
>;

export type ProjectsSidebarProps = {
  projects: SidebarProject[];
  initialCollapsed: boolean;
};

const COLLAPSE_COOKIE = "cassen_sb_collapsed";

function setCollapseCookie(value: boolean) {
  // 90-day persistence; user preference, not security.
  document.cookie = `${COLLAPSE_COOKIE}=${value ? "1" : "0"}; Max-Age=${
    60 * 60 * 24 * 90
  }; Path=/; SameSite=Lax`;
}

function projectLabel(p: SidebarProject): string {
  const title = (p.title ?? "").trim();
  if (title) return title;
  const prompt = (p.prompt ?? "").trim().replace(/\s+/g, " ");
  if (!prompt) return "Untitled project";
  return prompt.length > 60 ? prompt.slice(0, 60) + "…" : prompt;
}

/**
 * Persistent left sidebar (Claude-style). New-project CTA + recents
 * list + search + collapse toggle. Mobile: off-canvas drawer
 * triggered by a fixed top-left hamburger; route change auto-closes.
 *
 * Collapse state persists in `cassen_sb_collapsed` cookie so SSR
 * matches the user's last preference — no first-paint flicker.
 */
export function ProjectsSidebar({
  projects,
  initialCollapsed,
}: ProjectsSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(initialCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const [, startTransition] = useTransition();

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((c) => {
      const next = !c;
      setCollapseCookie(next);
      return next;
    });
  }, []);

  const filtered = filter
    ? projects.filter((p) =>
        projectLabel(p).toLowerCase().includes(filter.toLowerCase()),
      )
    : projects;

  return (
    <>
      {/* Mobile hamburger — only when sidebar closed */}
      <button
        type="button"
        onClick={() => setMobileOpen(true)}
        className="fixed left-3 top-3 z-30 grid h-9 w-9 place-items-center rounded-md border border-border bg-background/80 text-foreground backdrop-blur lg:hidden"
        aria-label="Open sidebar"
      >
        <PanelLeft className="h-4 w-4" />
      </button>

      {mobileOpen ? (
        <button
          type="button"
          onClick={() => setMobileOpen(false)}
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          aria-label="Close sidebar"
        />
      ) : null}

      <aside
        className={cn(
          "z-50 flex h-screen flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-[width,transform] duration-150",
          mobileOpen
            ? "fixed inset-y-0 left-0 w-72 translate-x-0 lg:translate-x-0"
            : "fixed inset-y-0 left-0 w-72 -translate-x-full lg:translate-x-0",
          "lg:relative lg:flex",
          collapsed ? "lg:w-14" : "lg:w-64",
        )}
      >
        {/* Header: brand + collapse toggle */}
        <div className="flex h-14 items-center justify-between gap-2 px-3">
          <Link
            href="/projects"
            className={cn(
              "flex items-center gap-2 overflow-hidden",
              collapsed && "lg:pointer-events-none lg:opacity-0",
            )}
          >
            <span className="grid h-7 w-7 flex-shrink-0 place-items-center rounded-md bg-primary/15 font-mono text-[10px] font-semibold text-primary">
              CA
            </span>
            <span className="truncate text-sm font-semibold text-sidebar-foreground">
              Cassen
            </span>
          </Link>
          <button
            type="button"
            onClick={toggleCollapsed}
            className="hidden h-8 w-8 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground lg:grid"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronsRight className="h-4 w-4" />
            ) : (
              <ChevronsLeft className="h-4 w-4" />
            )}
          </button>
          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            className="grid h-8 w-8 place-items-center rounded-md text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground lg:hidden"
            aria-label="Close sidebar"
          >
            <ChevronsLeft className="h-4 w-4" />
          </button>
        </div>

        {/* New project CTA */}
        <div className="px-3">
          <button
            type="button"
            onClick={() => startTransition(() => router.push("/projects/new"))}
            className={cn(
              "group flex w-full items-center gap-2 rounded-md border border-sidebar-border bg-sidebar/60 text-sm font-medium text-sidebar-foreground transition-colors hover:border-primary/40 hover:bg-sidebar-accent",
              collapsed ? "lg:justify-center lg:px-0 lg:py-2" : "px-3 py-2",
            )}
            title="New project"
          >
            <MessageSquarePlus className="h-4 w-4 flex-shrink-0" />
            <span className={collapsed ? "lg:hidden" : ""}>New project</span>
          </button>
        </div>

        {/* Search */}
        <div className={cn("px-3 pt-2", collapsed && "lg:hidden")}>
          <div className="flex items-center gap-2 rounded-md border border-sidebar-border bg-sidebar/50 px-2 py-1.5 text-xs text-muted-foreground focus-within:border-ring focus-within:text-sidebar-foreground">
            <Search className="h-3.5 w-3.5" />
            <input
              type="text"
              placeholder="Search projects"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="w-full bg-transparent text-sidebar-foreground placeholder:text-muted-foreground focus:outline-none"
            />
          </div>
        </div>

        {/* Recents */}
        <div
          className={cn(
            "mt-3 flex-1 overflow-y-auto px-2 pb-4",
            collapsed && "lg:px-1",
          )}
        >
          <p
            className={cn(
              "px-2 pb-1 text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground",
              collapsed && "lg:hidden",
            )}
          >
            Recents
          </p>
          <ul className="flex flex-col gap-0.5">
            {filtered.length === 0 ? (
              <li
                className={cn(
                  "px-2 py-3 text-xs text-muted-foreground",
                  collapsed && "lg:hidden",
                )}
              >
                No projects yet. Start one with &ldquo;New project&rdquo;.
              </li>
            ) : null}
            {filtered.map((p) => {
              const href = `/projects/${p.id}`;
              const isActive =
                pathname === href || pathname?.startsWith(`${href}/`);
              const label = projectLabel(p);
              return (
                <li key={p.id}>
                  <Link
                    href={href}
                    title={label}
                    className={cn(
                      "block truncate rounded-md text-sm transition-colors",
                      collapsed
                        ? "lg:mx-auto lg:flex lg:h-9 lg:w-9 lg:items-center lg:justify-center lg:p-0"
                        : "px-2 py-1.5",
                      isActive
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-sidebar-foreground hover:bg-sidebar-accent/60",
                    )}
                  >
                    <span className={collapsed ? "lg:hidden" : "block truncate"}>
                      {label}
                    </span>
                    <span
                      className={cn(
                        "hidden font-mono text-[10px] uppercase tracking-wider",
                        collapsed && "lg:inline",
                      )}
                      aria-hidden
                    >
                      {(label.match(/^[A-Za-z0-9]/)?.[0] || "·").toUpperCase()}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        {/* User account */}
        <div
          className={cn(
            "flex items-center gap-2 border-t border-sidebar-border px-3 py-3",
            collapsed && "lg:justify-center",
          )}
        >
          <UserButton
            appearance={{ elements: { avatarBox: "h-7 w-7" } }}
          />
          <span
            className={cn(
              "text-xs text-muted-foreground",
              collapsed && "lg:hidden",
            )}
          >
            Account
          </span>
        </div>
      </aside>
    </>
  );
}
