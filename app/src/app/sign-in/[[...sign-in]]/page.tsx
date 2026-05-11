import { SignIn } from "@clerk/nextjs";

export const metadata = { title: "Sign in" };

export default function Page() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <SignIn />
    </main>
  );
}
