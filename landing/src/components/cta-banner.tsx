"use client";

import { motion } from "motion/react";
import { SignupForm } from "@/components/signup-form";
import type { CtaContent, SignupContent } from "@/lib/content/types";

export function CtaBanner({
  content,
  signup,
}: {
  content: CtaContent;
  signup: SignupContent;
}) {
  return (
    <section className="relative w-full overflow-hidden bg-neutral-950 px-6 py-20 md:py-28">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-1/2 -translate-y-1/2 mx-auto h-[28rem] max-w-3xl bg-[radial-gradient(closest-side,rgba(120,119,198,0.18),transparent)] blur-3xl"
      />
      <div className="relative mx-auto max-w-3xl text-center">
        <motion.h2
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="text-balance text-4xl font-bold tracking-tight text-white md:text-5xl"
        >
          {content.headline}
        </motion.h2>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-4 text-lg text-neutral-400"
        >
          {content.subheadline}
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-10 flex flex-col items-center"
        >
          <SignupForm content={signup} className="mx-auto" />
          <p className="mt-4 text-sm text-neutral-500">{content.trust_line}</p>
        </motion.div>
      </div>
    </section>
  );
}
