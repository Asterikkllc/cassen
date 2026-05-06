import Image from "next/image";
import { hasRealUrl, safeHref } from "@/lib/safe-url";
import type { FooterContent } from "@/lib/content/types";

function fillTemplate(template: string, values: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, k) =>
    k in values ? String(values[k]) : `{${k}}`,
  );
}

const EMAIL_RE = /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/;

export function Footer({ content }: { content: FooterContent }) {
  const year = new Date().getFullYear();
  const copyright = fillTemplate(content.copyright_template, { year });
  const emailHref =
    content.contact_email && EMAIL_RE.test(content.contact_email.trim())
      ? `mailto:${content.contact_email.trim()}`
      : null;

  return (
    <footer className="w-full border-t border-neutral-900 bg-neutral-950 px-6 py-12">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 text-sm text-neutral-500 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <Image
            src="/logo.svg"
            alt=""
            width={28}
            height={28}
            className="h-7 w-7 rounded-md"
            priority={false}
          />
          <span className="text-base font-semibold tracking-tight text-neutral-200">
            {content.wordmark}
          </span>
          {content.tagline ? (
            <>
              <span className="hidden text-neutral-700 md:inline">·</span>
              <span className="hidden md:inline">{content.tagline}</span>
            </>
          ) : null}
        </div>
        <nav className="flex flex-wrap items-center gap-x-6 gap-y-2">
          {hasRealUrl(content.vision_url) && content.vision_label ? (
            <a
              href={safeHref(content.vision_url)}
              className="transition-colors hover:text-neutral-200"
            >
              {content.vision_label}
            </a>
          ) : null}
          {emailHref && content.contact_label ? (
            <a
              href={emailHref}
              className="transition-colors hover:text-neutral-200"
            >
              {content.contact_label}
            </a>
          ) : null}
          {hasRealUrl(content.twitter_url) && content.twitter_label ? (
            <a
              href={safeHref(content.twitter_url)}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-neutral-200"
            >
              {content.twitter_label}
            </a>
          ) : null}
        </nav>
        <div className="text-xs text-neutral-600">{copyright}</div>
      </div>
    </footer>
  );
}
