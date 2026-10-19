import type { Metadata } from "next";
import { ReviewWorkspace } from "@/components/review-workspace";

export const metadata: Metadata = {
  title: "Export Google Play Store reviews",
  description:
    "Download Google Play app reviews to CSV, Excel, or JSON. Paste a Play Store link and export in seconds with AppReviewr.",
};

export default function ExportPlayPage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <ReviewWorkspace
        heading="Export Google Play Store reviews"
        subheading="Paste a play.google.com link or package name, filter public reviews, and download CSV, Excel, or JSON."
        initialUrl="https://play.google.com/store/apps/details?id=com.spotify.music"
      />
    </main>
  );
}
