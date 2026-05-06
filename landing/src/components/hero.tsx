"use client";

import { motion } from "motion/react";
import { SignupForm } from "@/components/signup-form";
import { DotPattern } from "@/components/ui/dot-pattern";
import { AnimatedGradientText } from "@/components/ui/animated-gradient-text";
import { cn } from "@/lib/utils";
import type { HeroContent, SignupContent } from "@/lib/content/types";

export function Hero({
  content,
  signup,
}: {
  content: HeroContent;
  signup: SignupContent;
}) {
  return (
    <section className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-neutral-950 px-6 py-24">
      <DotPattern
        className={cn(
          "[mask-image:radial-gradient(ellipse_at_center,white,transparent_70%)]",
        )}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-1/3 -z-0 mx-auto h-[40rem] max-w-4xl bg-[radial-gradient(closest-side,rgba(120,119,198,0.18),transparent)] blur-3xl"
      />

      <div className="relative z-10 mx-auto flex max-w-3xl flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.05 }}
        >
          <AnimatedGradientText>{content.badge}</AnimatedGradientText>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mt-6 text-balance text-5xl font-bold tracking-tight text-white md:text-7xl"
        >
          {content.headline}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-6 max-w-2xl text-pretty text-lg text-neutral-400 md:text-xl"
        >
          {content.subheadline}
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.45 }}
          className="mt-10 w-full max-w-md"
        >
          <SignupForm content={signup} />
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-4 text-sm text-neutral-500"
        >
          {content.trust_line}
        </motion.p>
      </div>
    </section>
  );
}
