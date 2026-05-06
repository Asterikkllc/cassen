"use client";

import { motion } from "motion/react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { FaqContent } from "@/lib/content/types";

export function FAQ({ content }: { content: FaqContent }) {
  return (
    <section className="relative w-full bg-neutral-950 px-6 py-16 md:py-24">
      <div className="mx-auto max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-neutral-500">
            {content.eyebrow}
          </p>
          <h2 className="mt-4 text-balance text-4xl font-bold tracking-tight text-white md:text-5xl">
            {content.headline}
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-10"
        >
          <Accordion className="w-full">
            {content.items.map((item, idx) => (
              <AccordionItem key={idx} className="border-neutral-800">
                <AccordionTrigger className="text-left text-base font-medium text-white hover:text-white">
                  {item.q}
                </AccordionTrigger>
                <AccordionContent className="text-neutral-400">
                  {item.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  );
}
