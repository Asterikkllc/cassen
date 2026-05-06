"use client";

import { motion } from "motion/react";
import { resolveIcon } from "@/lib/content/icons";
import type { UseCasesContent } from "@/lib/content/types";

export function UseCases({ content }: { content: UseCasesContent }) {
  return (
    <section className="relative w-full bg-neutral-950 px-6 py-16 md:py-24">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-2xl text-center"
        >
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-500">
            {content.eyebrow}
          </p>
          <h2 className="mt-4 text-balance text-4xl font-bold tracking-tight text-white md:text-5xl">
            {content.headline}
          </h2>
          <p className="mt-4 text-pretty text-lg text-neutral-400">
            {content.subhead}
          </p>
        </motion.div>

        <div className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {content.items.map((uc, idx) => {
            const Icon = resolveIcon(uc.icon);
            return (
              <motion.div
                key={`${uc.title}-${idx}`}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.45, delay: (idx % 3) * 0.07 }}
                className="group rounded-2xl border border-neutral-800 bg-neutral-900/40 p-6 transition-all hover:-translate-y-0.5 hover:border-neutral-700 hover:bg-neutral-900/70"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-neutral-800 bg-neutral-900 text-neutral-300 transition-colors group-hover:border-neutral-700 group-hover:text-white">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 text-base font-semibold text-white">
                  {uc.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-400">
                  {uc.body}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
