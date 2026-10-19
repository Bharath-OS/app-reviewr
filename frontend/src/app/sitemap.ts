import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://appreviewr.local";
  return [
    { url: `${base}/`, changeFrequency: "weekly", priority: 1 },
    {
      url: `${base}/export-play-store-reviews`,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${base}/download-app-store-reviews`,
      changeFrequency: "monthly",
      priority: 0.8,
    },
  ];
}
