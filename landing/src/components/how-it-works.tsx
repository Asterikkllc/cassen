"use client";

import { motion } from "motion/react";
import { resolveIcon } from "@/lib/content/icons";
import type { HowItWorksContent } from "@/lib/content/types";

export function HowItWorks({ content }: { content: HowItWorksContent }) {
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

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
          {content.steps.map((step, idx) => {
            const Icon = resolveIcon(step.icon);
            return (
              <motion.div
                key={`${step.number}-${idx}`}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }}
                transition={{ duration: 0.5, delay: idx * 0.08 }}
                className="rounded-2xl border border-neutral-800 bg-neutral-900/50 p-7"
              >
                <div className="flex items-center gap-3 text-neutral-400">
                  <span className="text-sm font-medium tracking-widest">
                    {step.number}
                  </span>
                  <span className="h-px flex-1 bg-neutral-800" />
                  <Icon className="h-5 w-5 text-neutral-300" />
                </div>
                <h3 className="mt-6 text-xl font-semibold text-white">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-neutral-400">
                  {step.body}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
