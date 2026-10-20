import type { Metadata } from "next";
import Link from "next/link";
import { AppStoreWaitlistForm } from "@/components/app-store-waitlist-form";

export const metadata: Metadata = {
  title: "App Store review export — coming soon",
  description:
    "AppReviewr App Store review export is coming soon. Join the waitlist for CSV, Excel, and JSON downloads from apps.apple.com.",
};

const UPCOMING = [
  {
    title: "CSV, Excel, and JSON export",
    body: "Same download formats Play users get today — for spreadsheets and pipelines.",
  },
  {
    title: "Star, date, and keyword filters",
    body: "Narrow public reviews before you export, without manual cleanup.",
  },
  {
    title: "Multi-country storefronts",
    body: "Pull reviews across App Store regions (US, GB, and more) in one job.",
  },
  {
    title: "Preview before download",
    body: "Confirm the app and skim matching reviews on the page first.",
  },
  {
    title: "Honest coverage limits",
    body: "We’ll show how many public reviews Apple returns — never fake “all reviews.”",
  },
];

export default function AppStoreWaitlistPage() {
  return (
    <main>
      {/* First viewport: one composition — status, H1, one sentence, form CTA */}
      <section className="relative overflow-hidden border-b border-border/80">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_100%_0%,rgba(79,70,229,0.10),transparent_50%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)]"
        />
        <div className="relative mx-auto flex max-w-6xl flex-col gap-10 px-4 py-12 sm:px-6 sm:py-16 lg:grid lg:grid-cols-2 lg:items-center lg:gap-16 lg:py-20">
          <div className="space-y-5">
            <p className="text-sm font-medium text-primary">
              App Store export — coming soon
            </p>
            <h1 className="max-w-xl text-3xl font-semibold tracking-tight text-foreground sm:text-4xl lg:text-5xl lg:leading-[1.1]">
              Get App Store reviews the same way you get Play reviews
            </h1>
            <p className="max-w-md text-base leading-relaxed text-muted-foreground sm:text-lg">
              Built for iPhone and App Store teams: paste a link, filter public
              reviews, download CSV / Excel / JSON — no signup when it ships.
            </p>
          </div>

          <div className="w-full max-w-md lg:ml-auto lg:max-w-none">
            <div className="rounded-2xl border border-border bg-white p-6 shadow-sm sm:p-8">
              <h2 className="text-lg font-semibold text-foreground">
                Join the waitlist
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Free. No spam. We&apos;ll email you when it opens.
              </p>
              <div className="mt-6">
                <AppStoreWaitlistForm />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16">
        <div className="max-w-xl space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            What&apos;s coming for App Store
          </h2>
          <p className="text-sm text-muted-foreground sm:text-base">
            Planned for the first release — not available yet.
          </p>
        </div>
        <ul className="mt-8 divide-y divide-border border-t border-border sm:mt-10">
          {UPCOMING.map((item) => (
            <li
              key={item.title}
              className="flex flex-col gap-1 py-5 sm:flex-row sm:items-baseline sm:gap-8"
            >
              <h3 className="shrink-0 text-sm font-semibold text-foreground sm:w-56">
                {item.title}
              </h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {item.body}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="border-t border-border bg-muted/50">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-10 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p className="text-sm leading-relaxed text-muted-foreground">
            Need reviews today? Google Play export is live — free, no account.
          </p>
          <Link
            href="/"
            className="inline-flex h-11 min-h-11 shrink-0 items-center justify-center rounded-lg bg-primary px-5 text-sm font-medium text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            Open Play Store export
          </Link>
        </div>
      </section>
    </main>
  );
}
