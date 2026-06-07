import Script from "next/script";
import type { Metadata } from "next";
import { Inter } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const siteUrl = "https://complisenseai.com";
const description =
  "Automate DPDP compliance, AI governance, and audit readiness from one platform. Built for startups and mid-market teams.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "CompliSense-AI — AI-Native Compliance Platform",
  description,
  applicationName: "CompliSense-AI",
  keywords: [
    "DPDP compliance",
    "AI governance",
    "compliance software",
    "vendor compliance",
    "audit readiness",
    "policy management",
    "risk assessments",
  ],
  authors: [{ name: "CompliSense-AI" }],
  alternates: {
    canonical: siteUrl,
  },
  openGraph: {
    title: "CompliSense-AI — AI-Native Compliance Platform",
    description,
    url: siteUrl,
    siteName: "CompliSense-AI",
    type: "website",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "CompliSense-AI",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "CompliSense-AI — AI-Native Compliance Platform",
    description,
    images: ["/twitter-image"],
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    shortcut: "/favicon.svg",
    apple: "/favicon.svg",
  },
};

const organizationSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "CompliSense-AI",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: siteUrl,
  description,
  provider: {
    "@type": "Organization",
    name: "CompliSense-AI",
    url: siteUrl,
    email: "support@complisenseai.com",
  },
  featureList: [
    "DPDP compliance automation",
    "AI governance workflows",
    "Policy management",
    "Risk assessments",
    "Vendor compliance reviews",
    "Audit readiness",
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        <Script id="organization-schema" type="application/ld+json">
          {JSON.stringify(organizationSchema)}
        </Script>
        {children}
      </body>
    </html>
  );
}
