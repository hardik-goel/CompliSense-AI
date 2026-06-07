import { ImageResponse } from "next/og";

export const runtime = "edge";
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          width: "100%",
          height: "100%",
          padding: 56,
          background:
            "radial-gradient(circle at top, rgba(59,130,246,0.18), transparent 28%), linear-gradient(180deg, #0A0A0A 0%, #111111 100%)",
          color: "white",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            width: "100%",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: 32,
            padding: 40,
            background: "rgba(17,17,17,0.78)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 16,
                border: "1px solid rgba(255,255,255,0.12)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <span style={{ fontSize: 28 }}>✓</span>
            </div>
            <span style={{ fontSize: 28, fontWeight: 700 }}>CompliSense-AI</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 18, maxWidth: 760 }}>
            <span style={{ fontSize: 24, color: "#A1A1AA", letterSpacing: 2.5, textTransform: "uppercase" }}>
              AI-native compliance platform
            </span>
            <span style={{ fontSize: 72, lineHeight: 1.02, fontWeight: 700 }}>
              DPDP, AI governance, risk, and audit readiness in one system.
            </span>
          </div>
          <div style={{ display: "flex", gap: 14 }}>
            {["DPDP Ready", "AI Governance", "Vendor Reviews", "Audit Trails"].map((item) => (
              <div
                key={item}
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "10px 16px",
                  borderRadius: 999,
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "#D4D4D8",
                  fontSize: 22,
                }}
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>
    ),
    size,
  );
}
