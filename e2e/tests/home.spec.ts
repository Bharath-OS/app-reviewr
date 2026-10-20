import { expect, test } from "@playwright/test";

test.describe("AppReviewr home (mocked API)", () => {
  test.beforeEach(async ({ page }) => {
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
          rating: 4.5,
          rating_count: 1000,
          url: "https://play.google.com/store/apps/details?id=com.spotify.music",
        }),
      });
    });

    await page.route("**/api/jobs", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "job-demo",
            status: "completed",
            store: "google_play",
            app_id: "com.spotify.music",
            app_info: {
              store: "google_play",
              app_id: "com.spotify.music",
              name: "Spotify: Music and Podcasts",
              developer: "Spotify AB",
              icon_url: null,
              rating: 4.5,
              rating_count: 1000,
              url: null,
            },
            filters: { countries: ["us"], sort: "newest", max_reviews: 20 },
            progress: { fetched: 20, matched: 2, target: 20, message: "Done" },
            notes: [],
            review_count: 2,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
        return;
      }
      await route.fallback();
    });

    await page.route("**/api/jobs/job-demo", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "job-demo",
          status: "completed",
          store: "google_play",
          app_id: "com.spotify.music",
          app_info: {
            store: "google_play",
            app_id: "com.spotify.music",
            name: "Spotify: Music and Podcasts",
            developer: "Spotify AB",
            rating: 4.5,
            rating_count: 1000,
          },
          filters: { countries: ["us"], sort: "newest", max_reviews: 20 },
          progress: { fetched: 20, matched: 2, target: 20, message: "Done" },
          notes: [],
          review_count: 2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      });
    });

    await page.route("**/api/jobs/job-demo/reviews**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: "job-demo",
          total: 2,
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
              title: null,
              text: "Great music streaming",
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
              title: null,
              text: "Love the playlists",
              date: "2024-06-02T00:00:00Z",
              country: "US",
              language: "en",
            },
          ],
        }),
      });
    });
  });

  test("shows brand and fetches mocked reviews", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "AppReviewr" }).first()).toBeVisible();
    await expect(
      page.getByRole("heading", { name: /Export Google Play Store reviews/i }),
    ).toBeVisible();
    // Brand lives in the nav — no duplicate eyebrow above the H1.
    await expect(
      page.locator("main").getByText("AppReviewr", { exact: true }),
    ).toHaveCount(0);

    await page.getByLabel("App store URL").fill(
      "https://play.google.com/store/apps/details?id=com.spotify.music",
    );
    await page.getByTestId("preview-app").click();
    await expect(page.getByText("Spotify: Music and Podcasts")).toBeVisible();

    await page.getByRole("button", { name: "Fetch reviews" }).click();
    await expect(page.getByText("Results (2)")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Great music streaming")).toBeVisible();
    await expect(page.getByRole("link", { name: "Export CSV" })).toBeVisible();
  });

  test("Play and App Store nav routes", async ({ page }) => {
    await page.goto("/export-play-store-reviews");
    await expect(
      page.getByRole("heading", { name: /Export Google Play Store reviews/i }),
    ).toBeVisible();

    await page.getByRole("link", { name: "App Store" }).click();
    await expect(page).toHaveURL(/\/app-store-waitlist/);
    await expect(
      page.getByRole("heading", { name: /App Store export — join the waitlist/i }),
    ).toBeVisible();
    await expect(page.getByLabel("Name")).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(
      page.getByLabel(/What do you need App Store reviews for/i),
    ).toBeVisible();
    // Native form only — no embedded Google Form iframe.
    await expect(page.locator("iframe[title*='Google Form']")).toHaveCount(0);

    await page.goto("/download-app-store-reviews");
    await expect(page).toHaveURL(/\/app-store-waitlist/);
  });

  test("from/to date inputs cannot exceed today", async ({ page }) => {
    await page.goto("/");
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    const todayIso = `${yyyy}-${mm}-${dd}`;

    await expect(page.getByLabel("From date")).toHaveAttribute("max", todayIso);
    await expect(page.getByLabel("To date")).toHaveAttribute("max", todayIso);

    // Typed future dates should clamp to today.
    await page.getByLabel("To date").fill("2099-12-31");
    await expect(page.getByLabel("To date")).toHaveValue(todayIso);
  });

  test("empty max reviews blocks fetch and shows error", async ({ page }) => {
    let jobsPosted = 0;
    await page.route("**/api/jobs", async (route) => {
      if (route.request().method() === "POST") {
        jobsPosted += 1;
        await route.abort();
        return;
      }
      await route.fallback();
    });

    await page.goto("/");
    await page.getByLabel("App store URL").fill(
      "https://play.google.com/store/apps/details?id=com.spotify.music",
    );
    await page.getByLabel(/Max reviews/i).fill("");
    await page.getByRole("button", { name: "Fetch reviews" }).click();

    await expect(
      page.getByText(/Max reviews is empty or 0/i),
    ).toBeVisible({ timeout: 5000 });
    expect(jobsPosted).toBe(0);
  });
});
