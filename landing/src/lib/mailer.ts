import "server-only";
import nodemailer, { type Transporter } from "nodemailer";
import { renderWelcomeEmail } from "@/emails/welcome";
import { getSiteContent } from "@/lib/content/server";

let cachedTransporter: Transporter | null = null;

function getTransporter(): Transporter | null {
  if (cachedTransporter) return cachedTransporter;

  const host = process.env.SMTP_HOST;
  const port = Number(process.env.SMTP_PORT ?? 587);
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;
  const secure = process.env.SMTP_SECURE === "true" || port === 465;

  if (!host || !user || !pass) return null;

  cachedTransporter = nodemailer.createTransport({
    host,
    port,
    secure,
    auth: { user, pass },
  });

  return cachedTransporter;
}

export async function sendWelcomeEmail(
  to: string,
  position: number,
): Promise<{ sent: boolean; reason?: string }> {
  const transporter = getTransporter();
  if (!transporter) {
    return { sent: false, reason: "SMTP not configured" };
  }

  const content = await getSiteContent();
  const fromEmail = process.env.FROM_EMAIL ?? "hello@cassen.ai";
  const fromName = process.env.FROM_NAME ?? content.footer.wordmark;
  const { subject, html, text } = renderWelcomeEmail(
    position,
    content.welcome_email,
    content.footer.wordmark,
  );

  await transporter.sendMail({
    from: `"${fromName}" <${fromEmail}>`,
    to,
    subject,
    text,
    html,
    replyTo: fromEmail,
  });

  return { sent: true };
}
