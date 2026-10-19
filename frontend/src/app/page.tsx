import { ReviewWorkspace } from "@/components/review-workspace";
import { JsonLd, faqJsonLd } from "@/components/json-ld";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <JsonLd data={faqJsonLd()} />
      <ReviewWorkspace />
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
              No. Stores limit how many public reviews are available. AppReviewr
              shows exactly how many were returned and never claims “all reviews.”
            </p>
          </div>
          <div>
            <h3 className="font-medium text-foreground">
              Do you call Google on every Fetch?
            </h3>
            <p>
              Only on the first fetch (or after cache expires / Refresh from
              store). Reviews are cached for 12 hours per app, country, and sort
              order so repeat clicks are fast and kinder to the stores.
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
              Does App Store export always work?
            </h3>
            <p>
              App preview (lookup) usually works. Public App Store review RSS is
              often empty right now — we show that honestly. Google Play fetching
              is the most reliable path in Phase 1.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
