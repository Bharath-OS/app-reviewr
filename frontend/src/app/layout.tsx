import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/components/providers";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "AppReviewr — Download app store reviews",
    template: "%s · AppReviewr",
  },
  description:
    "Paste a Google Play or App Store link, fetch public reviews, filter them, and download CSV, Excel, or JSON. No signup.",
  metadataBase: new URL("https://appreviewr.local"),
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
        <Providers>
          <SiteHeader />
          {children}
        </Providers>
      </body>
    </html>
  );
}
