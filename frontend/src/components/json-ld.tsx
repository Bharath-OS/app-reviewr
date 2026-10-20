export function JsonLd({ data }: { data: Record<string, unknown> }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  );
}

export function websiteJsonLd(siteUrl: string) {
  return {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "AppReviewr",
    url: siteUrl,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description:
      "Download public Google Play reviews as CSV, Excel, or JSON. Paste a Play Store link, filter, and export — no signup.",
    offers: {
      "@type": "Offer",
      price: "0",
      priceCurrency: "USD",
    },
  };
}

export function faqJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: "Do I need an account to download app reviews?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "No. AppReviewr Phase 1 works without signup. Fair-use rate limits apply per IP.",
        },
      },
      {
        "@type": "Question",
        name: "Can I download all reviews for an app?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "No. Stores only expose a limited public set of reviews. AppReviewr shows how many were returned and never claims to export every review ever written.",
        },
      },
      {
        "@type": "Question",
        name: "What file formats can I export?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "CSV (UTF-8 with BOM for Excel), Excel (.xlsx), and JSON.",
        },
      },
      {
        "@type": "Question",
        name: "Are reviews cached?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Yes. After the first fetch for an app, country, sort, and star filter, AppReviewr caches reviews for 12 hours so repeat fetches do not re-scrape the store. Use Refresh from store to force a new scrape.",
        },
      },
    ],
  };
}
