/** Public support / feature-request contact (optional). */
export function getSupportEmail(): string {
  return process.env.NEXT_PUBLIC_SUPPORT_EMAIL?.trim() || "";
}

export function suggestFeatureMailto(email: string): string {
  const subject = encodeURIComponent("AppReviewr feature suggestion");
  const body = encodeURIComponent(
    "Hi AppReviewr team,\n\nI'd like to suggest:\n\n",
  );
  return `mailto:${email}?subject=${subject}&body=${body}`;
}

export function contactSupportMailto(email: string): string {
  const subject = encodeURIComponent("AppReviewr support");
  return `mailto:${email}?subject=${subject}`;
}
