"use client";

import { motion } from "motion/react";
import Image from "next/image";
import { ArrowUpRight } from "lucide-react";
import { hasRealUrl, safeHref } from "@/lib/safe-url";
import type { FounderContent } from "@/lib/content/types";

export function Founder({ content }: { content: FounderContent }) {
  return (
    <section className="relative w-full bg-neutral-950 px-6 py-16 md:py-24">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6 }}
          className="flex justify-center md:justify-start"
        >
          <div className="relative aspect-square w-full max-w-sm overflow-hidden rounded-3xl border border-neutral-800">
            {content.photo_url ? (
              <Image
                src={content.photo_url}
                alt={content.photo_alt}
                fill
                sizes="(max-width: 768px) 100vw, 384px"
                className="object-cover"
                priority={false}
              />
            ) : (
              <>
                <div className="absolute inset-0 bg-gradient-to-br from-neutral-700 via-neutral-800 to-neutral-950" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-6xl font-semibold tracking-tight text-neutral-200/70">
                    {content.initials}
                  </span>
                </div>
              </>
            )}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-500">
            {content.eyebrow}
          </p>
          <h2 className="mt-4 text-balance text-4xl font-bold tracking-tight text-white md:text-5xl">
            {content.heading}
          </h2>
          <div className="mt-6 space-y-4 text-neutral-300">
            {content.paragraphs.map((p, idx) => (
              <p key={idx}>{p}</p>
            ))}
          </div>
          {hasRealUrl(content.vision_memo_url) ? (
            <a
              href={safeHref(content.vision_memo_url)}
              className="mt-8 inline-flex items-center gap-2 text-sm font-medium text-white transition-colors hover:text-neutral-300"
            >
              {content.read_more_label}
              <ArrowUpRight className="h-4 w-4" />
            </a>
          ) : null}
        </motion.div>
      </div>
    </section>
  );
}
