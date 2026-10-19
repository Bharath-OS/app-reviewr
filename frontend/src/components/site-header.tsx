import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-border/80 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="text-lg font-semibold tracking-tight text-primary">
          AppReviewr
        </Link>
        <nav className="flex items-center gap-4 text-sm text-muted-foreground">
          <Link href="/export-play-store-reviews" className="hover:text-foreground">
            Play Store
          </Link>
          <Link href="/download-app-store-reviews" className="hover:text-foreground">
            App Store
          </Link>
        </nav>
      </div>
    </header>
  );
}
