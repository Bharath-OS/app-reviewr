/** Public Google Form waitlist config (baked in at build via NEXT_PUBLIC_*). */

export type GoogleFormWaitlistConfig = {
  actionUrl: string;
  entryName: string;
  entryEmail: string;
  entryMessage: string;
};

export function getGoogleFormWaitlistConfig(): GoogleFormWaitlistConfig {
  return {
    actionUrl: process.env.NEXT_PUBLIC_GOOGLE_FORM_ACTION_URL?.trim() || "",
    entryName: process.env.NEXT_PUBLIC_GOOGLE_FORM_ENTRY_NAME?.trim() || "",
    entryEmail: process.env.NEXT_PUBLIC_GOOGLE_FORM_ENTRY_EMAIL?.trim() || "",
    entryMessage:
      process.env.NEXT_PUBLIC_GOOGLE_FORM_ENTRY_MESSAGE?.trim() || "",
  };
}

export function isGoogleFormConfigured(cfg: GoogleFormWaitlistConfig): boolean {
  return Boolean(cfg.actionUrl && cfg.entryName && cfg.entryEmail);
}

/** Ensure action ends with /formResponse (accepts viewform paste too). */
export function toFormResponseUrl(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return "";
  try {
    const url = new URL(trimmed);
    if (url.pathname.includes("/viewform")) {
      url.pathname = url.pathname.replace(/\/viewform.*/, "/formResponse");
      url.search = "";
      url.hash = "";
    }
    return url.toString();
  } catch {
    return trimmed;
  }
}
