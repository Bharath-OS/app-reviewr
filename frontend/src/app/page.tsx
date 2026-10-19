import { ApiStatus } from "@/components/api-status";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--accent-soft),_transparent_55%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]">
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center px-6 py-16">
        <p className="text-sm font-semibold tracking-wide text-accent">
          AppReviewr
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          Download app reviews in seconds
        </h1>
        <p className="mt-4 max-w-xl text-lg text-muted">
          Paste a Google Play or App Store link, fetch public reviews, filter
          them, and export CSV, Excel, or JSON. No signup in Phase 1.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <span className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white">
            Review fetch UI coming next
          </span>
          <ApiStatus />
        </div>
      </div>
    </main>
  );
}
