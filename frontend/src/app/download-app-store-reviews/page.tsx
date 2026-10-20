import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "App Store waitlist",
  description:
    "App Store review export is coming soon. Join the AppReviewr waitlist.",
  alternates: {
    canonical: "/app-store-waitlist",
  },
};

/** Legacy App Store tool URL — redirected to the waitlist. */
export default function DownloadAppStorePage() {
  redirect("/app-store-waitlist");
}
