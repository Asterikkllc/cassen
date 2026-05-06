import Link from "next/link";
import Image from "next/image";
import { Show } from "@clerk/nextjs";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main className="flex flex-1 items-center justify-center px-6 py-24">
        <div className="flex max-w-2xl flex-col items-center text-center">
          <Image
            src="/logo.svg"
            alt=""
            width={72}
            height={72}
            className="h-18 w-18 rounded-2xl"
            priority
          />
          <h1 className="mt-8 text-balance text-4xl font-semibold tracking-tight text-white md:text-6xl">
            Describe what you want to build.
          </h1>
          <p className="mt-5 max-w-lg text-pretty text-base text-neutral-400 md:text-lg">
            Cassen turns plain-language descriptions into manufacturable
            hardware designs — parts ordered, prototypes assembled, firmware
            flashed, companion app generated.
          </p>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <Show when="signed-out">
              <Link
                href="/sign-up"
                className="inline-flex h-11 items-center justify-center rounded-full bg-white px-6 text-base font-medium text-neutral-950 transition-colors hover:bg-neutral-200"
              >
                Get started
              </Link>
              <Link
                href="/sign-in"
                className="inline-flex h-11 items-center justify-center rounded-full border border-white/10 bg-white/5 px-6 text-base font-medium text-neutral-200 transition-colors hover:bg-white/10"
              >
                Sign in
              </Link>
            </Show>
            <Show when="signed-in">
              <Link
                href="/projects"
                className="inline-flex h-11 items-center justify-center rounded-full bg-white px-6 text-base font-medium text-neutral-950 transition-colors hover:bg-neutral-200"
              >
                Continue to your projects
              </Link>
            </Show>
          </div>
        </div>
      </main>
    </>
  );
}
