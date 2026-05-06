import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://app.cassen.ai";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Cassen — Describe what you want to build.",
    template: "%s · Cassen",
  },
  description:
    "An AI agent for physical products. Describe a product, get a manufacturable design, parts ordered, prototype shipped.",
  applicationName: "Cassen",
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      appearance={{
        variables: {
          colorPrimary: "#10b981",
          colorBackground: "#0a0a0a",
          colorInputBackground: "rgba(255,255,255,0.04)",
          colorInputText: "#fafafa",
          colorText: "#fafafa",
          colorTextSecondary: "#a3a3a3",
          colorNeutral: "#fafafa",
          borderRadius: "0.625rem",
        },
        elements: {
          card: "bg-neutral-900/80 border border-neutral-800 backdrop-blur",
          headerTitle: "text-white",
          headerSubtitle: "text-neutral-400",
          socialButtonsBlockButton:
            "bg-neutral-900 border-neutral-800 hover:bg-neutral-800 text-neutral-100",
          formButtonPrimary:
            "bg-white text-neutral-950 hover:bg-neutral-200 normal-case",
          footerActionLink: "text-emerald-400 hover:text-emerald-300",
        },
      }}
    >
      <html
        lang="en"
        className={`dark ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      >
        <body className="min-h-full flex flex-col bg-neutral-950 text-neutral-100">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
