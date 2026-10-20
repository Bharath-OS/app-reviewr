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
      <div role="status" className="space-y-3">
        <h3 className="text-base font-semibold text-foreground">
          You&apos;re on the list
        </h3>
        <p className="text-sm text-muted-foreground">
          Thanks for joining. We&apos;ll email you when App Store export ships.
        </p>
        <Button
          type="button"
          variant="outline"
          className="mt-1"
          onClick={() => setDone(false)}
        >
          Submit another
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="waitlist-name">Name</Label>
        <Input
          id="waitlist-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Alex Founder"
          autoComplete="name"
          disabled={submitting}
          className="h-11 text-base md:text-sm"
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
          className="h-11 text-base md:text-sm"
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
          placeholder="Competitor research, ASO, support triage…"
          rows={3}
          disabled={submitting}
          className="flex min-h-[88px] w-full rounded-lg border border-input bg-transparent px-2.5 py-2.5 text-base outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50 md:text-sm"
        />
      </div>
      <Button
        type="submit"
        className="h-11 min-h-11 w-full text-base md:text-sm"
        disabled={submitting || configured === false}
      >
        {submitting ? "Submitting…" : "Notify me when it ships"}
      </Button>
      {configured === false && (
        <p className="text-xs text-muted-foreground" role="status">
          Waitlist signup is temporarily paused while we finish wiring
          notifications. Check back soon, or use{" "}
          <a href="/" className="font-medium text-primary underline-offset-4 hover:underline">
            Play Store export
          </a>{" "}
          today.
        </p>
      )}
    </form>
  );
}
