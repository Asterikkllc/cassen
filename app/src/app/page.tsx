import Image from "next/image";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-1 items-center justify-center px-6">
      <div className="flex max-w-xl flex-col items-center text-center">
        <Image
          src="/logo.svg"
          alt=""
          width={64}
          height={64}
          className="h-16 w-16 rounded-2xl"
          priority
        />
        <h1 className="mt-8 text-balance text-4xl font-semibold tracking-tight text-white md:text-5xl">
          Cassen Studio
        </h1>
        <p className="mt-4 text-pretty text-base text-neutral-400 md:text-lg">
          The product is being built. If you have early access, sign-in is coming
          soon. Otherwise, join the waitlist at{" "}
          <a
            href="https://cassen.ai"
            className="text-neutral-200 underline-offset-4 hover:underline"
          >
            cassen.ai
          </a>
          .
        </p>
      </div>
    </main>
  );
}
