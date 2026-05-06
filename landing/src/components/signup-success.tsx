"use client";

import { motion } from "motion/react";
import { Check } from "lucide-react";
import { track } from "@/lib/analytics";
import type { SignupContent } from "@/lib/content/types";

function buildShareUrl(text: string) {
  return `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
}

function fillTemplate(template: string, values: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, k) =>
    k in values ? String(values[k]) : `{${k}}`,
  );
}

type SignupSuccessProps = {
  position: number;
  content: SignupContent;
};

export function SignupSuccess({ position, content }: SignupSuccessProps) {
  const shareUrl = buildShareUrl(content.share_text);
  const positionLine = fillTemplate(content.success_position_template, { position });

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col items-center text-center"
    >
      <motion.div
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{
          type: "spring",
          stiffness: 320,
          damping: 18,
          delay: 0.05,
        }}
        className="relative flex h-14 w-14 items-center justify-center rounded-full border border-emerald-400/30 bg-emerald-400/10"
      >
        <span
          aria-hidden
          className="absolute inset-0 rounded-full bg-emerald-400/20 blur-xl"
        />
        <Check className="relative h-7 w-7 text-emerald-300" strokeWidth={3} />
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="mt-6 text-3xl font-semibold tracking-tight text-white md:text-4xl"
      >
        {content.success_heading}
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="mt-3 text-lg text-neutral-300"
      >
        {positionLine}
      </motion.p>

      <motion.p
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.4 }}
        className="mt-3 max-w-md text-sm text-neutral-400"
      >
        {content.success_body}
      </motion.p>

      <motion.a
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.55 }}
        href={shareUrl}
        target="_blank"
        rel="noopener noreferrer"
        onClick={() => track("share_clicked", { position })}
        className="mt-8 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm text-neutral-200 transition-colors hover:bg-white/10"
      >
        {content.share_label}
        <span aria-hidden>→</span>
      </motion.a>
    </motion.div>
  );
}
