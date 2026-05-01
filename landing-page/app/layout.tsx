import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CompliSense AI",
  description: "Regulatory compliance workflows for AI and data systems",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
