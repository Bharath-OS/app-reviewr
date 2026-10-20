import Link from "next/link";
import {
  contactSupportMailto,
  getSupportEmail,
  suggestFeatureMailto,
} from "@/lib/support";

export function SiteFooter() {
  const supportEmail = getSupportEmail();

  return (
    <footer className="border-t border-border/80 bg-white/70">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>
          © {new Date().getFullYear()} AppReviewr ·{" "}
          <Link href="/" className="hover:text-foreground">
            Play Store export
          </Link>
          {" · "}
          <Link href="/app-store-waitlist" className="hover:text-foreground">
            App Store waitlist
          </Link>
        </p>
        {supportEmail ? (
          <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <a
              href={suggestFeatureMailto(supportEmail)}
              className="font-medium text-primary underline-offset-4 hover:underline"
            >
              Suggest a feature
            </a>
            <span aria-hidden className="text-border">
              ·
            </span>
            <a
              href={contactSupportMailto(supportEmail)}
              className="hover:text-foreground"
            >
              {supportEmail}
            </a>
          </p>
        ) : null}
      </div>
    </footer>
  );
}
