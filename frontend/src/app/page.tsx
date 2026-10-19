import { ReviewWorkspace } from "@/components/review-workspace";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <ReviewWorkspace />
      <section className="mt-16 space-y-4 border-t border-border pt-10">
        <h2 className="text-xl font-semibold">FAQ</h2>
        <div className="space-y-4 text-sm text-muted-foreground">
          <div>
            <h3 className="font-medium text-foreground">Do I need an account?</h3>
            <p>No. Phase 1 is free to use with per-IP rate limits and job caps.</p>
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
              What formats can I download?
            </h3>
            <p>CSV (Excel-friendly UTF-8 BOM), Excel (.xlsx), and JSON.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
