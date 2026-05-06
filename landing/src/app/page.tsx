import { Hero } from "@/components/hero";
import { HowItWorks } from "@/components/how-it-works";
import { UseCases } from "@/components/use-cases";
import { Founder } from "@/components/founder";
import { FAQ } from "@/components/faq";
import { CtaBanner } from "@/components/cta-banner";
import { Footer } from "@/components/footer";
import { getSiteContent } from "@/lib/content/server";

export default async function Home() {
  const content = await getSiteContent();
  return (
    <main className="flex min-h-screen flex-1 flex-col">
      <Hero content={content.hero} signup={content.signup} />
      <HowItWorks content={content.how_it_works} />
      <UseCases content={content.use_cases} />
      <Founder content={content.founder} />
      <FAQ content={content.faq} />
      <CtaBanner content={content.cta} signup={content.signup} />
      <Footer content={content.footer} />
    </main>
  );
}
