import { NextResponse } from "next/server";

export const runtime = "nodejs";

type WaitlistBody = {
  name?: string;
  email?: string;
  message?: string;
};

function appsScriptUrl(): string {
  return process.env.APPS_SCRIPT_WAITLIST_URL?.trim() || "";
}

export async function GET() {
  const configured = Boolean(appsScriptUrl());
  return NextResponse.json({
    configured,
    message: configured
      ? "Waitlist API ready."
      : "Set APPS_SCRIPT_WAITLIST_URL to your Apps Script web app URL.",
  });
}

export async function POST(request: Request) {
  const scriptUrl = appsScriptUrl();
  if (!scriptUrl) {
    return NextResponse.json(
      {
        ok: false,
        error:
          "Waitlist is not configured. Set APPS_SCRIPT_WAITLIST_URL on the frontend server (see docs/app-store-waitlist-apps-script.md).",
      },
      { status: 503 },
    );
  }

  let body: WaitlistBody;
  try {
    body = (await request.json()) as WaitlistBody;
  } catch {
    return NextResponse.json(
      { ok: false, error: "Invalid JSON body." },
      { status: 400 },
    );
  }

  const name = (body.name || "").trim();
  const email = (body.email || "").trim();
  const message = (body.message || "").trim();

  if (!email) {
    return NextResponse.json(
      { ok: false, error: "Email is required." },
      { status: 400 },
    );
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json(
      { ok: false, error: "Enter a valid email address." },
      { status: 400 },
    );
  }
  if (name.length > 200 || email.length > 320 || message.length > 2000) {
    return NextResponse.json(
      { ok: false, error: "One or more fields are too long." },
      { status: 400 },
    );
  }

  try {
    const upstream = await fetch(scriptUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, message }),
      redirect: "follow",
      cache: "no-store",
    });

    const text = await upstream.text();
    let parsed: { ok?: boolean; already?: boolean; error?: string } = {};
    try {
      parsed = JSON.parse(text) as {
        ok?: boolean;
        already?: boolean;
        error?: string;
      };
    } catch {
      // Apps Script sometimes returns HTML on misconfigured deploy.
    }

    if (!upstream.ok || parsed.ok === false) {
      return NextResponse.json(
        {
          ok: false,
          error:
            parsed.error ||
            `Apps Script returned ${upstream.status}. Check the web app deploy (Anyone access) and Sheet permissions.`,
        },
        { status: 502 },
      );
    }

    return NextResponse.json({
      ok: true,
      already: Boolean(parsed.already),
    });
  } catch (err) {
    const detail = err instanceof Error ? err.message : "Upstream request failed";
    return NextResponse.json(
      {
        ok: false,
        error: `Could not reach Apps Script (${detail}).`,
      },
      { status: 502 },
    );
  }
}
