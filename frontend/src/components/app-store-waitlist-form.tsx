"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function normalizeFormUrl(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  try {
    const url = new URL(trimmed);
    // Prefer the embedded view when possible (works in an iframe).
    if (
      url.hostname.includes("docs.google.com") &&
      url.pathname.includes("/viewform") &&
      !url.searchParams.has("embedded")
    ) {
      url.searchParams.set("embedded", "true");
    }
    return url.toString();
  } catch {
    return trimmed;
  }
}

export function AppStoreWaitlistForm({ formUrl }: { formUrl: string }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const resolved = useMemo(() => normalizeFormUrl(formUrl), [formUrl]);
  const configured = Boolean(resolved);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!configured) {
      toast.error(
        "Waitlist form URL is not configured yet. Set NEXT_PUBLIC_APP_STORE_WAITLIST_FORM_URL.",
      );
      return;
    }
    if (!email.trim()) {
      toast.error("Enter your email so we can reach you.");
      return;
    }
    // Open the Google Form in a new tab. Prefill is optional — paste entry IDs
    // into the Form URL yourself (Google Forms → Get pre-filled link) if desired.
    const target = new URL(resolved);
    target.searchParams.delete("embedded");
    if (name.trim()) target.searchParams.set("usp", "pp_url");
    window.open(target.toString(), "_blank", "noopener,noreferrer");
    toast.success("Opened the waitlist form in a new tab — submit it there.");
  }

  return (
    <div className="space-y-8">
      <form onSubmit={onSubmit} className="max-w-md space-y-4">
        <div className="space-y-2">
          <Label htmlFor="waitlist-name">Name</Label>
          <Input
            id="waitlist-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Alex Founder"
            autoComplete="name"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="waitlist-email">Email</Label>
          <Input
            id="waitlist-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            autoComplete="email"
          />
        </div>
        <Button type="submit" className="h-11 w-full sm:w-auto" disabled={!configured}>
          Join the waitlist
        </Button>
        {!configured && (
          <p className="text-sm text-amber-800" role="status">
            Form URL not set. Add{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">
              NEXT_PUBLIC_APP_STORE_WAITLIST_FORM_URL
            </code>{" "}
            to <code className="rounded bg-muted px-1 py-0.5 text-xs">.env.local</code>{" "}
            with your Google Form link, then rebuild / restart the frontend.
          </p>
        )}
      </form>

      {configured && (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Or fill the Google Form below /{" "}
            <a
              href={resolved.replace("embedded=true", "").replace(/[?&]$/, "")}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-primary underline-offset-4 hover:underline"
            >
              open it in a new tab
            </a>
            .
          </p>
          <div className="overflow-hidden rounded-xl border border-border bg-white">
            <iframe
              title="App Store waitlist Google Form"
              src={resolved}
              className="h-[640px] w-full"
              loading="lazy"
            />
          </div>
        </div>
      )}
    </div>
  );
}
