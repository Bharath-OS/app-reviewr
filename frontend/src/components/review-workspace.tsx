"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  cancelJob,
  createJob,
  exportUrl,
  fetchAppInfo,
  getJob,
  listReviews,
  type AppInfo,
  type JobFilters,
  type JobResponse,
  type Review,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const DEFAULT_FILTERS: JobFilters = {
  ratings: null,
  countries: ["us"],
  languages: null,
  date_from: null,
  date_to: null,
  keyword: null,
  has_developer_reply: null,
  sort: "newest",
  max_reviews: 100,
};

const COUNTRY_OPTIONS = ["us", "gb", "ca", "au", "in", "de", "fr", "jp", "br", "mx"];

function stars(n: number) {
  return "★".repeat(n) + "☆".repeat(5 - n);
}

export function ReviewWorkspace({
  initialUrl = "",
  heading,
  subheading,
}: {
  initialUrl?: string;
  heading?: string;
  subheading?: string;
}) {
  const [url, setUrl] = useState(initialUrl);
  const [filters, setFilters] = useState<JobFilters>(DEFAULT_FILTERS);
  const [selectedRatings, setSelectedRatings] = useState<number[]>([]);
  const [appInfo, setAppInfo] = useState<AppInfo | null>(null);
  const [appLoading, setAppLoading] = useState(false);
  const [appError, setAppError] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 25;
  const [busy, setBusy] = useState(false);

  const progressPct = useMemo(() => {
    if (!job) return 0;
    const target = job.progress.target || filters.max_reviews || 1;
    return Math.min(100, Math.round((job.progress.matched / target) * 100));
  }, [job, filters.max_reviews]);

  const jobId = job?.id;
  const jobStatus = job?.status;

  useEffect(() => {
    if (!jobId || !jobStatus || !["queued", "running"].includes(jobStatus)) return;
    const id = window.setInterval(async () => {
      try {
        const next = await getJob(jobId);
        setJob(next);
        if (["completed", "failed", "cancelled"].includes(next.status)) {
          window.clearInterval(id);
          if (next.status === "completed") {
            toast.success(`Fetched ${next.review_count} reviews`);
          } else if (next.status === "failed") {
            toast.error(next.error?.message || "Fetch failed");
          }
        }
      } catch (err) {
        window.clearInterval(id);
        toast.error(err instanceof Error ? err.message : "Polling failed");
      }
    }, 700);
    return () => window.clearInterval(id);
  }, [jobId, jobStatus]);

  useEffect(() => {
    if (!jobId || !jobStatus || !["completed", "cancelled"].includes(jobStatus)) {
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const pageData = await listReviews(jobId, page, pageSize);
        if (!cancelled) {
          setReviews(pageData.reviews);
          setTotal(pageData.total);
        }
      } catch (err) {
        if (!cancelled) {
          toast.error(err instanceof Error ? err.message : "Could not load reviews");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [jobId, jobStatus, page]);

  async function onPreview() {
    setAppError(null);
    setAppInfo(null);
    if (!url.trim()) {
      setAppError("Paste a Google Play or App Store link (or app ID).");
      return;
    }
    setAppLoading(true);
    try {
      const info = await fetchAppInfo(url.trim());
      setAppInfo(info);
    } catch (err) {
      setAppError(err instanceof Error ? err.message : "Could not load app");
    } finally {
      setAppLoading(false);
    }
  }

  async function onFetch(forceRefresh = false) {
    if (!url.trim()) {
      toast.error("Paste a store link first");
      return;
    }
    setBusy(true);
    setReviews([]);
    setTotal(0);
    setPage(1);
    try {
      const payload: JobFilters = {
        ...filters,
        ratings: selectedRatings.length ? selectedRatings : null,
        countries: filters.countries.length ? filters.countries : ["us"],
        keyword: filters.keyword?.trim() || null,
      };
      const created = await createJob(url.trim(), payload, { forceRefresh });
      setJob(created);
      if (!appInfo && created.app_info) setAppInfo(created.app_info);
      if (forceRefresh) {
        toast.message("Refreshing from the store…");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not start job");
    } finally {
      setBusy(false);
    }
  }

  async function onCancel() {
    if (!job) return;
    try {
      const cancelled = await cancelJob(job.id);
      setJob(cancelled);
      toast.message("Fetch cancelled");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Cancel failed");
    }
  }

  function toggleCountry(cc: string) {
    setFilters((prev) => {
      const set = new Set(prev.countries);
      if (set.has(cc)) set.delete(cc);
      else set.add(cc);
      const countries = Array.from(set);
      return { ...prev, countries: countries.length ? countries : ["us"] };
    });
  }

  function toggleRating(r: number) {
    setSelectedRatings((prev) =>
      prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r].sort(),
    );
  }

  const running = job?.status === "running" || job?.status === "queued";
  const canExport =
    job &&
    ["completed", "cancelled"].includes(job.status) &&
    (job.review_count > 0 || total > 0);

  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <div>
          <p className="text-sm font-semibold tracking-wide text-primary">AppReviewr</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            {heading || "Download app reviews in seconds"}
          </h1>
          <p className="mt-3 max-w-2xl text-muted-foreground">
            {subheading ||
              "Paste a Google Play or App Store link, filter public reviews, preview them, and export CSV, Excel, or JSON. No signup."}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://play.google.com/store/apps/details?id=… or apps.apple.com/…/id…"
            className="h-11 flex-1"
            aria-label="App store URL"
          />
          <Button
            type="button"
            variant="secondary"
            className="h-11"
            data-testid="preview-app"
            onClick={onPreview}
            disabled={appLoading}
          >
            {appLoading ? "Looking up…" : "Preview app"}
          </Button>
          <Button
            type="button"
            className="h-11"
            onClick={() => void onFetch(false)}
            disabled={busy || running}
          >
            {running ? "Fetching…" : "Fetch reviews"}
          </Button>
          <Button
            type="button"
            variant="outline"
            className="h-11"
            onClick={() => void onFetch(true)}
            disabled={busy || running}
            title="Bypass the 12-hour cache and scrape the store again"
          >
            Refresh from store
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          First fetch scrapes the store and caches reviews for 12 hours. A second
          Fetch for the same app/country/sort uses the cache (no Google/Apple
          call). Use <span className="font-medium text-foreground">Refresh from store</span>{" "}
          for a fresh scrape.
        </p>
        {appError && (
          <p className="text-sm text-destructive" role="alert">
            {appError}
          </p>
        )}
      </section>

      {appInfo && (
        <section className="flex flex-wrap items-center gap-4 rounded-xl border border-border bg-white p-4 shadow-sm">
          {appInfo.icon_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={appInfo.icon_url}
              alt=""
              className="h-16 w-16 rounded-2xl border border-border object-cover"
            />
          ) : (
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-accent text-primary">
              App
            </div>
          )}
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="truncate text-lg font-semibold">{appInfo.name}</h2>
              <Badge variant="secondary">
                {appInfo.store === "google_play" ? "Google Play" : "App Store"}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {appInfo.developer || "Unknown developer"}
              {appInfo.rating != null && (
                <>
                  {" · "}
                  {appInfo.rating.toFixed(2)}★
                  {appInfo.rating_count != null &&
                    ` (${appInfo.rating_count.toLocaleString()} ratings)`}
                </>
              )}
            </p>
          </div>
        </section>
      )}

      <section className="space-y-4 rounded-xl border border-border bg-white p-4 sm:p-6">
        <h2 className="text-base font-semibold">Filters</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-2">
            <Label>Star ratings</Label>
            <div className="flex flex-wrap gap-2">
              {[5, 4, 3, 2, 1].map((r) => (
                <label key={r} className="flex items-center gap-1.5 text-sm">
                  <Checkbox
                    checked={selectedRatings.includes(r)}
                    onCheckedChange={() => toggleRating(r)}
                  />
                  {r}★
                </label>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="keyword">Keyword</Label>
            <Input
              id="keyword"
              value={filters.keyword || ""}
              onChange={(e) =>
                setFilters((f) => ({ ...f, keyword: e.target.value || null }))
              }
              placeholder="crash, love, subscription…"
            />
          </div>
          <div className="space-y-2">
            <Label>Sort</Label>
            <Select
              value={filters.sort}
              onValueChange={(v) =>
                setFilters((f) => ({
                  ...f,
                  sort: v as JobFilters["sort"],
                }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Newest</SelectItem>
                <SelectItem value="most_relevant">Most relevant</SelectItem>
                <SelectItem value="rating">Rating</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="max">Max reviews</Label>
            <Input
              id="max"
              type="number"
              min={1}
              max={2000}
              value={filters.max_reviews}
              onChange={(e) =>
                setFilters((f) => ({
                  ...f,
                  max_reviews: Math.min(2000, Math.max(1, Number(e.target.value) || 1)),
                }))
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="from">From date</Label>
            <Input
              id="from"
              type="date"
              value={filters.date_from || ""}
              onChange={(e) =>
                setFilters((f) => ({ ...f, date_from: e.target.value || null }))
              }
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="to">To date</Label>
            <Input
              id="to"
              type="date"
              value={filters.date_to || ""}
              onChange={(e) =>
                setFilters((f) => ({ ...f, date_to: e.target.value || null }))
              }
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Countries</Label>
            <div className="flex flex-wrap gap-2">
              {COUNTRY_OPTIONS.map((cc) => (
                <label
                  key={cc}
                  className="inline-flex items-center gap-1.5 rounded-md border border-border px-2 py-1 text-xs uppercase"
                >
                  <Checkbox
                    checked={filters.countries.includes(cc)}
                    onCheckedChange={() => toggleCountry(cc)}
                  />
                  {cc}
                </label>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              Multi-country fetch runs in one job (max 10).
            </p>
          </div>
          <div className="space-y-2">
            <Label>Developer reply</Label>
            <Select
              value={
                filters.has_developer_reply == null
                  ? "any"
                  : filters.has_developer_reply
                    ? "yes"
                    : "no"
              }
              onValueChange={(v) =>
                setFilters((f) => ({
                  ...f,
                  has_developer_reply:
                    v === "any" ? null : v === "yes" ? true : false,
                }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                <SelectItem value="yes">Has reply</SelectItem>
                <SelectItem value="no">No reply</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </section>

      {job && (
        <section className="space-y-3 rounded-xl border border-border bg-white p-4 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Progress</h2>
              <p className="text-sm text-muted-foreground">
                {job.progress.message || job.status}
                {job.progress.current_country
                  ? ` · ${job.progress.current_country}`
                  : ""}
                {" · "}
                matched {job.progress.matched}
                {job.progress.target ? ` / ${job.progress.target}` : ""}
                {" · fetched "}
                {job.progress.fetched}
              </p>
            </div>
            {running && (
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </div>
          <Progress value={progressPct} />
          {job.served_from_cache && (
            <Badge variant="secondary">Served from 12h cache</Badge>
          )}
          {job.notes?.map((n) => (
            <p
              key={n.code}
              className={`text-sm rounded-md border px-3 py-2 ${
                n.code === "served_from_cache"
                  ? "border-emerald-100 bg-emerald-50 text-emerald-900"
                  : "border-amber-100 bg-amber-50 text-amber-800"
              }`}
            >
              {n.message}
            </p>
          ))}
          {job.error && (
            <p className="text-sm text-destructive" role="alert">
              {job.error.message}
            </p>
          )}
        </section>
      )}

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-base font-semibold">
            Results{total ? ` (${total})` : ""}
          </h2>
          <div className="flex flex-wrap gap-2">
            {(["csv", "xlsx", "json"] as const).map((fmt) =>
              canExport && job ? (
                <a
                  key={fmt}
                  href={exportUrl(job.id, fmt)}
                  download
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
                >
                  Export {fmt.toUpperCase()}
                </a>
              ) : (
                <Button key={fmt} variant="outline" size="sm" disabled>
                  Export {fmt.toUpperCase()}
                </Button>
              ),
            )}
          </div>
        </div>

        {!job && (
          <p className="text-sm text-muted-foreground">
            Preview an app and fetch reviews to see results here.
          </p>
        )}
        {job && ["completed", "cancelled"].includes(job.status) && total === 0 && (
          <p className="text-sm text-muted-foreground">
            No reviews matched your filters
            {job.store === "app_store"
              ? " (App Store RSS may also return an empty public feed)."
              : "."}
          </p>
        )}

        {reviews.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-border bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rating</TableHead>
                  <TableHead>Author</TableHead>
                  <TableHead>Review</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Country</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {reviews.map((r) => (
                  <TableRow key={`${r.review_id}-${r.country}`}>
                    <TableCell className="whitespace-nowrap text-amber-500">
                      {stars(r.rating)}
                    </TableCell>
                    <TableCell className="max-w-[8rem] truncate">{r.author}</TableCell>
                    <TableCell className="min-w-[16rem] max-w-xl">
                      {r.title && (
                        <div className="font-medium text-foreground">{r.title}</div>
                      )}
                      <div className="line-clamp-3 text-sm text-muted-foreground">
                        {r.text}
                      </div>
                      {r.developer_reply && (
                        <div className="mt-1 text-xs text-primary">
                          Dev reply: {r.developer_reply}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="whitespace-nowrap text-sm">
                      {r.date.slice(0, 10)}
                    </TableCell>
                    <TableCell className="uppercase text-sm">{r.country}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {total > pageSize && (
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page} of {Math.ceil(total / pageSize)}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= Math.ceil(total / pageSize)}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}
