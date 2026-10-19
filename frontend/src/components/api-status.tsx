"use client";

import { useEffect, useState } from "react";

type Status = "loading" | "ok" | "error";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8741";

export function ApiStatus() {
  const [status, setStatus] = useState<Status>("loading");
  const [detail, setDetail] = useState("Checking API…");

  useEffect(() => {
    let cancelled = false;

    async function check() {
      try {
        const res = await fetch(`${API_URL}/api/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as { service?: string; status?: string };
        if (cancelled) return;
        setStatus("ok");
        setDetail(`${data.service ?? "API"} ${data.status ?? "ok"}`);
      } catch {
        if (cancelled) return;
        setStatus("error");
        setDetail("API offline — start the backend on :8741");
      }
    }

    void check();
    return () => {
      cancelled = true;
    };
  }, []);

  const tone =
    status === "ok"
      ? "border-emerald-200 bg-emerald-50 text-emerald-800"
      : status === "error"
        ? "border-rose-200 bg-rose-50 text-rose-800"
        : "border-border bg-surface text-muted";

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm ${tone}`}
      role="status"
      aria-live="polite"
    >
      <span
        className={`h-2 w-2 rounded-full ${
          status === "ok"
            ? "bg-emerald-500"
            : status === "error"
              ? "bg-rose-500"
              : "bg-slate-400"
        }`}
      />
      {detail}
    </span>
  );
}
