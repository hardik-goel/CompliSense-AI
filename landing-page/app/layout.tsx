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
  "@type": "Organization",
  "@id": `${siteUrl}/#organization`,
  name: "CompliSense-AI",
  url: siteUrl,
  logo: `${siteUrl}/logo.png`,
  description,
  email: "support@complisenseai.com",
  sameAs: [] as string[],
};

const websiteSchema = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": `${siteUrl}/#website`,
  name: "CompliSense-AI",
  url: siteUrl,
  description,
  publisher: { "@id": `${siteUrl}/#organization` },
  inLanguage: "en",
};

const softwareSchema = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "@id": `${siteUrl}/#software`,
  name: "CompliSense-AI",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  url: siteUrl,
  description,
  publisher: { "@id": `${siteUrl}/#organization` },
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "GBP",
    description: "Free tier — full EU AI Act & DPDP core, 10 scans/month, no credit card.",
    url: `${siteUrl}/#pricing`,
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
        <Script id="website-schema" type="application/ld+json">
          {JSON.stringify(websiteSchema)}
        </Script>
        <Script id="software-schema" type="application/ld+json">
          {JSON.stringify(softwareSchema)}
        </Script>
        {children}
      </body>
    </html>
  );
}
