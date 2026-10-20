import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/components/providers";
import { SiteHeader } from "@/components/site-header";
import { JsonLd, websiteJsonLd } from "@/components/json-ld";
import { getSiteUrl } from "@/lib/site";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const siteUrl = getSiteUrl();

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "AppReviewr — Export Google Play Store reviews",
    template: "%s · AppReviewr",
  },
  description:
    "Paste a Google Play link, fetch public reviews, filter them, and download CSV, Excel, or JSON. Free, no signup.",
  keywords: [
    "download app reviews",
    "Google Play reviews CSV",
    "export Play Store reviews",
    "app review scraper",
    "AppReviewr",
  ],
  authors: [{ name: "AppReviewr" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteUrl,
    siteName: "AppReviewr",
    title: "AppReviewr — Export Google Play Store reviews",
    description:
      "Fetch public Google Play reviews and export CSV, Excel, or JSON in seconds.",
  },
  twitter: {
    card: "summary_large_image",
    title: "AppReviewr — Export Google Play Store reviews",
    description:
      "Paste a Play Store link, filter public reviews, and export CSV, Excel, or JSON.",
  },
  robots: {
    index: true,
    follow: true,
  },
  alternates: {
    canonical: siteUrl,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} min-h-screen bg-[radial-gradient(ellipse_at_top,_#eef2ff,_transparent_50%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] antialiased`}
      >
        <JsonLd data={websiteJsonLd(siteUrl)} />
        <Providers>
          <SiteHeader />
          {children}
        </Providers>
      </body>
    </html>
  );
}
