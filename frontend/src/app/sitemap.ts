import type { MetadataRoute } from "next";
import { getSiteUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = getSiteUrl();
  return [
    { url: `${base}/`, changeFrequency: "weekly", priority: 1 },
    {
      url: `${base}/export-play-store-reviews`,
      changeFrequency: "monthly",
      priority: 0.8,
    },
    {
      url: `${base}/app-store-waitlist`,
      changeFrequency: "monthly",
      priority: 0.7,
    },
  ];
}
