import type { Metadata, Viewport } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Analytics } from "@vercel/analytics/react";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Cassen",
    template: "%s · Cassen",
  },
  description:
    "Describe a physical product in plain language. Cassen designs, validates, sources, and ships it.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL ?? "https://app.cassen.ai",
  ),
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0a0a",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider
      // App is dark-first; tell Clerk's components to match the
      // theme so the sign-in/up surfaces don't flash white.
      appearance={{
        variables: {
          colorPrimary: "#22d3ee",
          colorBackground: "#0a0a0a",
          colorText: "#fafafa",
          colorInputBackground: "#1a1a1a",
          colorInputText: "#fafafa",
          borderRadius: "0.625rem",
        },
      }}
    >
      <html lang="en" className="dark">
        <body className="min-h-screen bg-background text-foreground antialiased">
          {children}
          <Analytics />
        </body>
      </html>
    </ClerkProvider>
  );
}
