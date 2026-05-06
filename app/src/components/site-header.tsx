import Link from "next/link";
import Image from "next/image";
import { Show, UserButton } from "@clerk/nextjs";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 w-full border-b border-neutral-900/80 bg-neutral-950/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <Image
            src="/logo.svg"
            alt=""
            width={28}
            height={28}
            className="h-7 w-7 rounded-md"
            priority
          />
          <span className="text-base font-semibold tracking-tight text-neutral-100">
            Cassen
          </span>
        </Link>

        <nav className="flex items-center gap-3">
          <Show when="signed-out">
            <Link
              href="/sign-in"
              className="text-sm text-neutral-300 transition-colors hover:text-white"
            >
              Sign in
            </Link>
            <Link
              href="/sign-up"
              className="rounded-full bg-white px-4 py-1.5 text-sm font-medium text-neutral-950 transition-colors hover:bg-neutral-200"
            >
              Sign up
            </Link>
          </Show>
          <Show when="signed-in">
            <Link
              href="/projects"
              className="text-sm text-neutral-300 transition-colors hover:text-white"
            >
              Projects
            </Link>
            <UserButton
              appearance={{
                elements: { avatarBox: "h-8 w-8" },
              }}
            />
          </Show>
        </nav>
      </div>
    </header>
  );
}
