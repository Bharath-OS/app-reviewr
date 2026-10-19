/** Public site origin for canonical URLs, sitemap, and JSON-LD. */
export function getSiteUrl(): string {
  return (
    process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "") ||
    "https://appreviewr.local"
  );
}
