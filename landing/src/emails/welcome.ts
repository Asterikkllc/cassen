import type { WelcomeEmailContent as ContentSpec } from "@/lib/content/types";

type RenderedEmail = {
  subject: string;
  html: string;
  text: string;
};

function fillTemplate(template: string, values: Record<string, string | number>) {
  return template.replace(/\{(\w+)\}/g, (_, k) =>
    k in values ? String(values[k]) : `{${k}}`,
  );
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function renderWelcomeEmail(
  position: number,
  content: ContentSpec,
  wordmark: string,
): RenderedEmail {
  const subject = content.subject;
  const positionLine = fillTemplate(content.position_line_template, {
    position,
  });

  const textLines = [
    content.greeting,
    "",
    positionLine,
    "",
    ...content.body_paragraphs.flatMap((p) => [p, ""]),
    content.signature,
  ];
  const text = textLines.join("\n");

  const bodyParasHtml = content.body_paragraphs
    .map(
      (p) =>
        `<p style="margin:0 0 16px;">${escapeHtml(p)}</p>`,
    )
    .join("\n");

  const html = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>${escapeHtml(subject)}</title>
  </head>
  <body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#111;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f5f5f5;padding:40px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width:600px;background:#ffffff;border-radius:12px;padding:40px;box-shadow:0 1px 2px rgba(0,0,0,0.04);">
            <tr>
              <td style="font-size:14px;color:#666;letter-spacing:0.08em;text-transform:uppercase;padding-bottom:16px;">
                ${escapeHtml(wordmark)}
              </td>
            </tr>
            <tr>
              <td style="font-size:16px;line-height:1.6;color:#111;">
                <p style="margin:0 0 16px;">${escapeHtml(content.greeting)}</p>
                <p style="margin:0 0 16px;">${escapeHtml(positionLine)}</p>
                ${bodyParasHtml}
                <p style="margin:24px 0 0;">${escapeHtml(content.signature)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding-top:32px;border-top:1px solid #eee;margin-top:32px;font-size:12px;color:#999;line-height:1.5;">
                ${escapeHtml(content.footer_disclaimer)}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>`;

  return { subject, html, text };
}
