import type { Metadata } from "next";
import { redirect } from "next/navigation";

export const metadata: Metadata = {
  title: "Export Google Play Store reviews",
  description:
    "Download Google Play app reviews to CSV, Excel, or JSON. Paste a Play Store link and export in seconds with AppReviewr.",
  alternates: {
    canonical: "/",
  },
};

/** Legacy intent URL — Play export now lives on `/`. */
export default function ExportPlayPage() {
  redirect("/");
}
