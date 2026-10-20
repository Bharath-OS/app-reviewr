"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function AppStoreWaitlistForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/waitlist");
        const data = (await res.json()) as { configured?: boolean };
        if (!cancelled) setConfigured(Boolean(data.configured));
      } catch {
        if (!cancelled) setConfigured(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      toast.error("Enter your email so we can reach you.");
      return;
    }

    setSubmitting(true);
    setDone(false);
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          email: trimmedEmail,
          message: message.trim() || undefined,
        }),
      });
      const data = (await res.json().catch(() => ({}))) as {
        ok?: boolean;
        error?: string;
      };
      if (!res.ok || !data.ok) {
        toast.error(data.error || "Could not join the waitlist. Try again.");
        return;
      }
      setDone(true);
      setName("");
      setEmail("");
      setMessage("");
      toast.success("You're on the waitlist — thanks!");
    } catch {
      toast.error("Network error. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div
        className="max-w-md rounded-xl border border-border bg-white p-6 shadow-sm"
        role="status"
      >
        <h2 className="text-lg font-semibold text-foreground">You're on the list</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Thanks for joining. We'll email you when App Store export ships.
        </p>
        <Button
          type="button"
          variant="outline"
          className="mt-4"
          onClick={() => setDone(false)}
        >
          Submit another
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="max-w-md space-y-4">
      <div className="space-y-2">
        <Label htmlFor="waitlist-name">Name</Label>
        <Input
          id="waitlist-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Alex Founder"
          autoComplete="name"
          disabled={submitting}
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
          disabled={submitting}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="waitlist-need">
          What do you need App Store reviews for?{" "}
          <span className="font-normal text-muted-foreground">(optional)</span>
        </Label>
        <textarea
          id="waitlist-need"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Competitor research, App Store Optimization, support triage…"
          rows={3}
          disabled={submitting}
          className="flex w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50"
        />
      </div>
      <Button
        type="submit"
        className="h-11 w-full sm:w-auto"
        disabled={submitting || configured === false}
      >
        {submitting ? "Submitting…" : "Join the waitlist"}
      </Button>
      {configured === false && (
        <p className="text-sm text-amber-800" role="status">
          Waitlist backend is not configured. Set{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            APPS_SCRIPT_WAITLIST_URL
          </code>{" "}
          in{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            frontend/.env.local
          </code>{" "}
          (server-side — not{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">NEXT_PUBLIC_</code>
          ), then restart the frontend. See{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            docs/app-store-waitlist-apps-script.md
          </code>
          .
        </p>
      )}
    </form>
  );
}
