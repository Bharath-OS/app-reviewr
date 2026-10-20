import type { Metadata } from "next";
import { AppStoreWaitlistForm } from "@/components/app-store-waitlist-form";

export const metadata: Metadata = {
  title: "App Store waitlist",
  description:
    "App Store review export is coming soon. Join the AppReviewr waitlist to get notified.",
};

export default function AppStoreWaitlistPage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
      <section className="max-w-2xl space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          App Store export — join the waitlist
        </h1>
        <p className="text-muted-foreground">
          Google Play export is live today. Apple App Store review download is
          next — leave your email and we will notify you when it ships. No
          account required.
        </p>
      </section>
      <div className="mt-10">
        <AppStoreWaitlistForm />
      </div>
    </main>
  );
}
