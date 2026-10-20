"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { suggestFeatureMailto } from "@/lib/support";

const STORAGE_KEY = "appreviewr-app-store-waitlist-joined";

type JoinState = {
  at: string;
  email?: string;
};

function readJoined(): JoinState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as JoinState;
    if (!parsed?.at) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeJoined(email: string) {
  const payload: JoinState = {
    at: new Date().toISOString(),
    email: email.trim().toLowerCase(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

export function AppStoreWaitlistForm({
  supportEmail = "",
}: {
  supportEmail?: string;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [joined, setJoined] = useState<JoinState | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [alreadyOnServer, setAlreadyOnServer] = useState(false);

  useEffect(() => {
    setJoined(readJoined());
    setHydrated(true);
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
    if (joined) return;

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      toast.error("Enter your email so we can reach you.");
      return;
    }

    setSubmitting(true);
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
        already?: boolean;
        error?: string;
      };
      if (!res.ok || !data.ok) {
        toast.error(data.error || "Could not join the waitlist. Try again.");
        return;
      }

      writeJoined(trimmedEmail);
      setJoined(readJoined());
      setAlreadyOnServer(Boolean(data.already));
      setName("");
      setEmail("");
      setMessage("");
      if (data.already) {
        toast.message("You're already on the waitlist.");
      } else {
        toast.success("You're on the waitlist — check your email.");
      }
    } catch {
      toast.error("Network error. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (!hydrated) {
    return (
      <div className="h-48 animate-pulse rounded-lg bg-muted/60" aria-hidden />
    );
  }

  if (joined) {
    return (
      <div role="status" className="space-y-4">
        <div className="space-y-2">
          <h3 className="text-base font-semibold text-foreground">
            You&apos;re on the list
          </h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {alreadyOnServer
              ? "This email was already registered — we didn't add a duplicate. We'll still notify you when App Store export ships."
              : "Thanks for joining the App Store waitlist. We sent a short thank-you note to your inbox (check spam if you don't see it). We'll email you again when export opens."}
          </p>
          {joined.email ? (
            <p className="text-xs text-muted-foreground">
              Signed up as{" "}
              <span className="font-medium text-foreground">{joined.email}</span>
            </p>
          ) : null}
        </div>
        {supportEmail ? (
          <a
            href={suggestFeatureMailto(supportEmail)}
            className="inline-flex h-11 min-h-11 items-center justify-center rounded-lg border border-border bg-white px-4 text-sm font-medium text-foreground hover:bg-muted/60"
          >
            Suggest a feature
          </a>
        ) : null}
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
      {supportEmail ? (
        <p className="text-xs text-muted-foreground">
          Have an idea already?{" "}
          <a
            href={suggestFeatureMailto(supportEmail)}
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Suggest a feature
          </a>
        </p>
      ) : null}
      {configured === false && (
        <p className="text-xs text-muted-foreground" role="status">
          Waitlist signup is temporarily paused while we finish wiring
          notifications. Check back soon, or use{" "}
          <a
            href="/"
            className="font-medium text-primary underline-offset-4 hover:underline"
          >
            Play Store export
          </a>{" "}
          today.
        </p>
      )}
    </form>
  );
}
