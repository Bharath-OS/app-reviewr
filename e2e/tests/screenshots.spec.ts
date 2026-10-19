import { test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const OUT_DIRS = [
  path.resolve("/workspace/docs/screenshots"),
  path.resolve(
    "/cursor/stores/bc-1e7ada91-f4dd-45ed-8045-778df9775dd9/media/screenshots",
  ),
];

function save(buffer: Buffer, name: string) {
  for (const dir of OUT_DIRS) {
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, name), buffer);
  }
}

test("capture product screenshots", async ({ page }) => {
  await page.route("**/api/app-info**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        store: "google_play",
        app_id: "com.spotify.music",
        name: "Spotify: Music and Podcasts",
        developer: "Spotify AB",
        icon_url: null,
        rating: 4.35,
        rating_count: 36500000,
        url: null,
      }),
    });
  });

  await page.route("**/api/jobs", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "shot-job",
        status: "completed",
        store: "google_play",
        app_id: "com.spotify.music",
        app_info: {
          store: "google_play",
          app_id: "com.spotify.music",
          name: "Spotify: Music and Podcasts",
          developer: "Spotify AB",
          rating: 4.35,
          rating_count: 36500000,
        },
        filters: { countries: ["us"], sort: "newest", max_reviews: 20 },
        progress: { fetched: 20, matched: 3, target: 20, message: "Done" },
        notes: [],
        review_count: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    });
  });

  await page.route("**/api/jobs/shot-job", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "shot-job",
        status: "completed",
        store: "google_play",
        app_id: "com.spotify.music",
        app_info: {
          store: "google_play",
          app_id: "com.spotify.music",
          name: "Spotify: Music and Podcasts",
          developer: "Spotify AB",
          rating: 4.35,
          rating_count: 36500000,
        },
        filters: { countries: ["us"], sort: "newest", max_reviews: 20 },
        progress: { fetched: 20, matched: 3, target: 20, message: "Done" },
        notes: [],
        review_count: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
    });
  });

  await page.route("**/api/jobs/shot-job/reviews**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        job_id: "shot-job",
        total: 3,
        page: 1,
        page_size: 25,
        reviews: [
          {
            store: "google_play",
            app_id: "com.spotify.music",
            app_name: "Spotify",
            review_id: "1",
            author: "Alice",
            rating: 5,
            text: "Great music streaming experience.",
            date: "2024-06-01T00:00:00Z",
            country: "US",
            language: "en",
          },
          {
            store: "google_play",
            app_id: "com.spotify.music",
            app_name: "Spotify",
            review_id: "2",
            author: "Bob",
            rating: 4,
            text: "Love the playlists and podcasts.",
            date: "2024-06-02T00:00:00Z",
            country: "US",
            language: "en",
          },
          {
            store: "google_play",
            app_id: "com.spotify.music",
            app_name: "Spotify",
            review_id: "3",
            author: "Cara",
            rating: 3,
            text: "Good app but ads are frequent.",
            date: "2024-06-03T00:00:00Z",
            country: "US",
            language: "en",
          },
        ],
      }),
    });
  });

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto("/");
  save(await page.screenshot({ fullPage: true }), "01-home.png");

  await page.getByLabel("App store URL").fill(
    "https://play.google.com/store/apps/details?id=com.spotify.music",
  );
  await page.getByTestId("preview-app").click();
  await page.getByText("Spotify: Music and Podcasts").waitFor();
  save(await page.screenshot({ fullPage: true }), "02-play-preview.png");

  await page.getByRole("button", { name: "Fetch reviews" }).click();
  await page.getByText("Results (3)").waitFor();
  save(await page.screenshot({ fullPage: true }), "03-play-results.png");

  await page.goto("/export-play-store-reviews");
  save(await page.screenshot({ fullPage: true }), "04-intent-play.png");

  await page.goto("/download-app-store-reviews");
  save(await page.screenshot({ fullPage: true }), "05-intent-appstore.png");

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  save(await page.screenshot({ fullPage: true }), "06-home-mobile.png");
});
