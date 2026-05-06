import type { Metadata } from "next";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/next";
import { AnalyticsProvider } from "@/components/analytics-provider";
import { getSiteContent } from "@/lib/content/server";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://cassen.ai";

export async function generateMetadata(): Promise<Metadata> {
  const content = await getSiteContent();
  const { title, description } = content.meta;
  const wordmark = content.footer.wordmark;

  return {
    metadataBase: new URL(SITE_URL),
    title: {
      default: title,
      template: `%s · ${wordmark}`,
    },
    description,
    applicationName: wordmark,
    keywords: [
      "hardware design",
      "AI hardware",
      "manufacturable design",
      "AI engineer",
      "BOM generation",
      "PCB",
      "CAD",
      wordmark,
    ],
    openGraph: {
      type: "website",
      url: SITE_URL,
      siteName: wordmark,
      title,
      description,
      locale: "en_US",
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
    robots: { index: true, follow: true },
  };
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const plausibleDomain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN;

  return (
    <html
      lang="en"
      className={`dark ${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        {plausibleDomain ? (
          <Script
            defer
            data-domain={plausibleDomain}
            src="https://plausible.io/js/script.js"
            strategy="afterInteractive"
          />
        ) : null}
      </head>
      <body className="min-h-full flex flex-col bg-neutral-950 text-neutral-100">
        <AnalyticsProvider>{children}</AnalyticsProvider>
        <Analytics />
      </body>
    </html>
  );
}
