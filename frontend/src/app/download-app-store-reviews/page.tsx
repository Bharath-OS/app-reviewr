import type { Metadata } from "next";
import { ReviewWorkspace } from "@/components/review-workspace";

export const metadata: Metadata = {
  title: "Download App Store reviews",
  description:
    "Download Apple App Store reviews to CSV, Excel, or JSON. Paste an App Store link and export with AppReviewr.",
};

export default function DownloadAppStorePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <ReviewWorkspace
        heading="Download App Store reviews"
        subheading="Paste an apps.apple.com link or numeric Apple ID. Tier 1 uses the public iTunes RSS feed (~500 reviews/country when available)."
        initialUrl="https://apps.apple.com/us/app/spotify-music-and-podcasts/id324684580"
      />
    </main>
  );
}
