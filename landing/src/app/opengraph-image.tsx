import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Cassen — Describe a product. Get a manufacturable design back.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px",
          background: "#0a0a0a",
          color: "#fafafa",
          fontFamily: "system-ui, sans-serif",
          backgroundImage:
            "radial-gradient(circle at 25% 35%, rgba(120,119,198,0.20), transparent 55%), radial-gradient(circle at 75% 80%, rgba(56,189,248,0.12), transparent 55%)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            fontSize: 24,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "#a3a3a3",
          }}
        >
          <div
            style={{
              width: 12,
              height: 12,
              borderRadius: 999,
              background: "#34d399",
            }}
          />
          Cassen · Pre-launch
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 24,
          }}
        >
          <div
            style={{
              fontSize: 84,
              fontWeight: 700,
              lineHeight: 1.05,
              letterSpacing: "-0.02em",
              color: "#fafafa",
            }}
          >
            Describe a product.
            <br />
            Get a manufacturable design back.
          </div>
          <div
            style={{
              fontSize: 28,
              color: "#a3a3a3",
              maxWidth: 880,
              lineHeight: 1.35,
            }}
          >
            An AI agent for physical products — CAD, BOMs, firmware, all from a
            sentence.
          </div>
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: 22,
            color: "#737373",
          }}
        >
          <div>cassen.ai</div>
          <div>Join the waitlist →</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
