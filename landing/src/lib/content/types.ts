export type HeroContent = {
  badge: string;
  headline: string;
  subheadline: string;
  trust_line: string;
};

export type FounderContent = {
  eyebrow: string;
  heading: string;
  paragraphs: string[];
  photo_url: string | null;
  photo_alt: string;
  vision_memo_url: string;
  read_more_label: string;
  initials: string;
};

export type HowItWorksStep = {
  number: string;
  icon: string;
  title: string;
  body: string;
};

export type HowItWorksContent = {
  eyebrow: string;
  headline: string;
  subhead: string;
  steps: HowItWorksStep[];
};

export type UseCaseItem = {
  icon: string;
  title: string;
  body: string;
};

export type UseCasesContent = {
  eyebrow: string;
  headline: string;
  subhead: string;
  items: UseCaseItem[];
};

export type FaqItem = { q: string; a: string };

export type FaqContent = {
  eyebrow: string;
  headline: string;
  items: FaqItem[];
};

export type CtaContent = {
  headline: string;
  subheadline: string;
  trust_line: string;
};

export type FooterContent = {
  wordmark: string;
  tagline: string;
  vision_url: string;
  vision_label: string;
  contact_email: string;
  contact_label: string;
  twitter_url: string;
  twitter_label: string;
  copyright_template: string;
};

export type SignupContent = {
  email_placeholder: string;
  submit_label: string;
  submit_pending_label: string;
  success_heading: string;
  success_position_template: string;
  success_body: string;
  share_label: string;
  share_text: string;
  error_invalid_email: string;
  error_duplicate: string;
  error_generic: string;
  error_not_configured: string;
};

export type WelcomeEmailContent = {
  subject: string;
  greeting: string;
  position_line_template: string;
  body_paragraphs: string[];
  signature: string;
  footer_disclaimer: string;
};

export type MetaContent = {
  title: string;
  description: string;
};

export type SiteContent = {
  hero: HeroContent;
  founder: FounderContent;
  how_it_works: HowItWorksContent;
  use_cases: UseCasesContent;
  faq: FaqContent;
  cta: CtaContent;
  footer: FooterContent;
  signup: SignupContent;
  welcome_email: WelcomeEmailContent;
  meta: MetaContent;
};

export type SectionKey = keyof SiteContent;
