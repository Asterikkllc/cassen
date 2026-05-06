import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { getSiteContent } from "@/lib/content/server";
import { HeroForm } from "@/components/admin/sections/hero-form";
import { FounderForm } from "@/components/admin/sections/founder-form";
import {
  HowItWorksForm,
  UseCasesForm,
  FaqForm,
} from "@/components/admin/sections/list-form";
import { CtaForm, FooterForm } from "@/components/admin/sections/cta-form";
import { SignupSettingsForm } from "@/components/admin/sections/signup-form";
import { WelcomeEmailForm } from "@/components/admin/sections/welcome-email-form";
import { MetaForm } from "@/components/admin/sections/meta-form";

export const dynamic = "force-dynamic";

export default async function AdminContentPage() {
  const content = await getSiteContent();

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-12 text-neutral-100">
      <div className="mx-auto max-w-4xl">
        <Link
          href="/admin"
          className="inline-flex items-center gap-2 text-sm text-neutral-400 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to waitlist
        </Link>

        <div className="mt-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-white">
              Site content
            </h1>
            <p className="mt-2 text-sm text-neutral-400">
              Edit the landing page sections. Changes go live on the next page
              load.
            </p>
          </div>
        </div>

        <div className="mt-8">
          <Tabs defaultValue="hero">
            <TabsList variant="line" className="mb-8 flex-wrap gap-2">
              <TabsTrigger value="meta">Meta</TabsTrigger>
              <TabsTrigger value="hero">Hero</TabsTrigger>
              <TabsTrigger value="how_it_works">How it works</TabsTrigger>
              <TabsTrigger value="use_cases">Use cases</TabsTrigger>
              <TabsTrigger value="founder">Founder</TabsTrigger>
              <TabsTrigger value="faq">FAQ</TabsTrigger>
              <TabsTrigger value="cta">CTA</TabsTrigger>
              <TabsTrigger value="footer">Footer</TabsTrigger>
              <TabsTrigger value="signup">Signup form</TabsTrigger>
              <TabsTrigger value="welcome_email">Welcome email</TabsTrigger>
            </TabsList>

            <TabsContent value="meta">
              <MetaForm initial={content.meta} />
            </TabsContent>
            <TabsContent value="hero">
              <HeroForm initial={content.hero} />
            </TabsContent>
            <TabsContent value="how_it_works">
              <HowItWorksForm initial={content.how_it_works} />
            </TabsContent>
            <TabsContent value="use_cases">
              <UseCasesForm initial={content.use_cases} />
            </TabsContent>
            <TabsContent value="founder">
              <FounderForm initial={content.founder} />
            </TabsContent>
            <TabsContent value="faq">
              <FaqForm initial={content.faq} />
            </TabsContent>
            <TabsContent value="cta">
              <CtaForm initial={content.cta} />
            </TabsContent>
            <TabsContent value="footer">
              <FooterForm initial={content.footer} />
            </TabsContent>
            <TabsContent value="signup">
              <SignupSettingsForm initial={content.signup} />
            </TabsContent>
            <TabsContent value="welcome_email">
              <WelcomeEmailForm initial={content.welcome_email} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </main>
  );
}
