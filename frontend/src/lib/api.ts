export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8741";

export type Store = "google_play" | "app_store";
export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type AppInfo = {
  store: Store;
  app_id: string;
  name: string;
  developer?: string | null;
  icon_url?: string | null;
  rating?: number | null;
  rating_count?: number | null;
  url?: string | null;
};

export type JobFilters = {
  ratings?: number[] | null;
  countries: string[];
  languages?: string[] | null;
  date_from?: string | null;
  date_to?: string | null;
  keyword?: string | null;
  has_developer_reply?: boolean | null;
  sort: "newest" | "most_relevant" | "rating";
  max_reviews: number;
};

export type JobResponse = {
  id: string;
  status: JobStatus;
  store: Store;
  app_id: string;
  app_info?: AppInfo | null;
  filters: JobFilters;
  progress: {
    fetched: number;
    matched: number;
    target?: number | null;
    current_country?: string | null;
    message?: string | null;
  };
  error?: { code: string; message: string } | null;
  notes: { code: string; message: string }[];
  review_count: number;
};

export type Review = {
  store: Store;
  app_id: string;
  app_name: string;
  review_id: string;
  author: string;
  rating: number;
  title?: string | null;
  text: string;
  date: string;
  app_version?: string | null;
  thumbs_up?: number | null;
  developer_reply?: string | null;
  reply_date?: string | null;
  country: string;
  language?: string | null;
};

export type ReviewsPage = {
  job_id: string;
  total: number;
  page: number;
  page_size: number;
  reviews: Review[];
};

type ApiError = { error: { code: string; message: string } };

async function parseJson<T>(res: Response): Promise<T> {
  const data = await res.json();
  if (!res.ok) {
    const err = data as ApiError;
    throw new Error(err.error?.message || `Request failed (${res.status})`);
  }
  return data as T;
}

export async function fetchAppInfo(url: string): Promise<AppInfo> {
  const res = await fetch(
    `${API_URL}/api/app-info?url=${encodeURIComponent(url)}`,
  );
  return parseJson<AppInfo>(res);
}

export async function createJob(
  url: string,
  filters: JobFilters,
): Promise<JobResponse> {
  const res = await fetch(`${API_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, filters }),
  });
  return parseJson<JobResponse>(res);
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`);
  return parseJson<JobResponse>(res);
}

export async function cancelJob(jobId: string): Promise<JobResponse> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}/cancel`, {
    method: "POST",
  });
  return parseJson<JobResponse>(res);
}

export async function listReviews(
  jobId: string,
  page = 1,
  pageSize = 25,
): Promise<ReviewsPage> {
  const res = await fetch(
    `${API_URL}/api/jobs/${jobId}/reviews?page=${page}&page_size=${pageSize}`,
  );
  return parseJson<ReviewsPage>(res);
}

export function exportUrl(
  jobId: string,
  format: "csv" | "xlsx" | "json",
): string {
  return `${API_URL}/api/jobs/${jobId}/export?format=${format}`;
}
