import type { Metadata } from "next";
import { ReviewWorkspace } from "@/components/review-workspace";
import { JsonLd, faqJsonLd } from "@/components/json-ld";

export const metadata: Metadata = {
  title: "Export Google Play Store reviews",
  description:
    "Download Google Play app reviews to CSV, Excel, or JSON. Paste a Play Store link and export in seconds with AppReviewr.",
};

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <JsonLd data={faqJsonLd()} />
      <ReviewWorkspace
        heading="Export Google Play Store reviews"
        subheading="Paste a play.google.com link or package name, filter public reviews, and download CSV, Excel, or JSON."
        initialUrl="https://play.google.com/store/apps/details?id=com.spotify.music"
      />
      <section className="mt-16 space-y-4 border-t border-border pt-10">
        <h2 className="text-xl font-semibold">FAQ</h2>
        <div className="space-y-4 text-sm text-muted-foreground">
          <div>
            <h3 className="font-medium text-foreground">Do I need an account?</h3>
            <p>
              No. Phase 1 is free with fair-use limits per IP (about 10 fresh
              scrapes per hour). Cached re-fetches of the same app within 12 hours
              do not use that scrape quota.
            </p>
          </div>
          <div>
            <h3 className="font-medium text-foreground">
              Will I get every review?
            </h3>
            <p>
              No. Google Play limits how many public reviews are available.
              AppReviewr shows exactly how many were returned and never claims
              “all reviews.”
            </p>
          </div>
          <div>
            <h3 className="font-medium text-foreground">
              Do you call Google on every Fetch?
            </h3>
            <p>
              Only on the first fetch (or after cache expires / Refresh from
              store). Reviews are cached for 12 hours per app, country, sort, and
              star filter so repeat clicks are fast and kinder to the store.
            </p>
          </div>
          <div>
            <h3 className="font-medium text-foreground">
              What formats can I download?
            </h3>
            <p>CSV (Excel-friendly UTF-8 BOM), Excel (.xlsx), and JSON.</p>
          </div>
          <div>
            <h3 className="font-medium text-foreground">
              What about the App Store?
            </h3>
            <p>
              App Store export is on the waitlist for now. Use the App Store link
              in the nav to join — Google Play export is the primary tool today.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
