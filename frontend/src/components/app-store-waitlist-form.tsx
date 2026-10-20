"use client";

import { useId, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  isGoogleFormConfigured,
  toFormResponseUrl,
  type GoogleFormWaitlistConfig,
} from "@/lib/google-form";

/**
 * POST to Google Forms via a hidden iframe target.
 * Browser CORS blocks reading the response; the iframe submit still lands in
 * the Form / linked Sheet — the reliable client-only pattern.
 */
function postToGoogleForm(
  actionUrl: string,
  fields: Record<string, string>,
  iframeName: string,
) {
  let iframe = document.querySelector<HTMLIFrameElement>(
    `iframe[name="${iframeName}"]`,
  );
  if (!iframe) {
    iframe = document.createElement("iframe");
    iframe.name = iframeName;
    iframe.title = "Hidden Google Form target";
    iframe.style.display = "none";
    document.body.appendChild(iframe);
  }

  const form = document.createElement("form");
  form.method = "POST";
  form.action = actionUrl;
  form.target = iframeName;
  form.acceptCharset = "UTF-8";
  form.style.display = "none";

  for (const [name, value] of Object.entries(fields)) {
    if (!name || value === undefined) continue;
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = value;
    form.appendChild(input);
  }

  document.body.appendChild(form);
  form.submit();
  form.remove();
}

export function AppStoreWaitlistForm({
  config,
}: {
  config: GoogleFormWaitlistConfig;
}) {
  const iframeName = useId().replace(/:/g, "") + "-gform";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  const configured = isGoogleFormConfigured(config);
  const actionUrl = toFormResponseUrl(config.actionUrl);
  const showMessage = Boolean(config.entryMessage);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!configured || !actionUrl) {
      toast.error(
        "Waitlist is not configured. Set NEXT_PUBLIC_GOOGLE_FORM_ACTION_URL and entry IDs in .env.local.",
      );
      return;
    }
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      toast.error("Enter your email so we can reach you.");
      return;
    }

    setSubmitting(true);
    setDone(false);

    const fields: Record<string, string> = {
      [config.entryName]: name.trim(),
      [config.entryEmail]: trimmedEmail,
      // Helps some Forms skip the confirmation interstitial.
      submit: "Submit",
    };
    if (showMessage && message.trim()) {
      fields[config.entryMessage] = message.trim();
    }

    try {
      postToGoogleForm(actionUrl, fields, iframeName);
      // Opaque cross-origin response — treat submit as success after a beat.
      await new Promise((r) => window.setTimeout(r, 600));
      setDone(true);
      setName("");
      setEmail("");
      setMessage("");
      toast.success("You're on the waitlist — thanks!");
    } catch {
      toast.error("Something went wrong. Please try again in a moment.");
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
      {showMessage && (
        <div className="space-y-2">
          <Label htmlFor="waitlist-message">Message (optional)</Label>
          <textarea
            id="waitlist-message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="What do you need App Store export for?"
            rows={3}
            disabled={submitting}
            className="flex w-full rounded-lg border border-input bg-transparent px-2.5 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-50"
          />
        </div>
      )}
      <Button
        type="submit"
        className="h-11 w-full sm:w-auto"
        disabled={!configured || submitting}
      >
        {submitting ? "Submitting…" : "Join the waitlist"}
      </Button>
      {!configured && (
        <p className="text-sm text-amber-800" role="status">
          Set{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            NEXT_PUBLIC_GOOGLE_FORM_ACTION_URL
          </code>
          ,{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            NEXT_PUBLIC_GOOGLE_FORM_ENTRY_NAME
          </code>
          , and{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            NEXT_PUBLIC_GOOGLE_FORM_ENTRY_EMAIL
          </code>{" "}
          in{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">.env.local</code>
          , then rebuild / restart the frontend. See the README for how to find
          entry IDs.
        </p>
      )}
    </form>
  );
}
