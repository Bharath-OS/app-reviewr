# App Store waitlist → Google Apps Script → Sheet + thank-you email

Browser → `POST /api/waitlist` (Next.js) → Apps Script web app →:

1. If the email is **new**: append a Sheet row, send a thank-you email (`GmailApp`), return `{ ok: true }`.
2. If the email **already exists**: do **not** append, return `{ ok: true, already: true }` (no second thank-you).

The Script deploy URL stays **server-side** (`APPS_SCRIPT_WAITLIST_URL`).

The browser also stores a local “already joined” flag so the form is not shown again on that device.

## 1. Create a Google Sheet

1. Open [Google Sheets](https://sheets.google.com) → **Blank spreadsheet**.
2. Rename it e.g. `AppReviewr App Store Waitlist`.
3. Headers in row 1:

| A | B | C | D |
|---|---|---|---|
| Timestamp | Name | Email | Need |

4. Rename the tab to `Waitlist`.

## 2. Paste this Apps Script (replace any older version)

1. Sheet → **Extensions → Apps Script**.
2. Paste **all** of the following:

```javascript
/**
 * AppReviewr waitlist receiver
 * - Dedupes by email (column C)
 * - Sends thank-you email on NEW signups only (GmailApp)
 *
 * Deploy: Web app → Execute as: Me → Who has access: Anyone
 * Re-authorize after first deploy so Gmail send is allowed.
 */
var SHEET_NAME = "Waitlist";
var EMAIL_COL = 3; // C = Email

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || "{}";
    var data = JSON.parse(raw);
    var name = String(data.name || "").trim();
    var email = String(data.email || "").trim().toLowerCase();
    var message = String(data.message || "").trim();

    if (!email) {
      return json_({ ok: false, error: "Email is required." });
    }

    var sheet = getWaitlistSheet_();
    if (emailExists_(sheet, email)) {
      return json_({ ok: true, already: true });
    }

    sheet.appendRow([new Date(), name, email, message]);
    sendThankYou_(name, email);
    return json_({ ok: true, already: false });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function doGet() {
  return json_({ ok: true, service: "AppReviewr waitlist" });
}

function getWaitlistSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(["Timestamp", "Name", "Email", "Need"]);
  }
  return sheet;
}

function emailExists_(sheet, email) {
  var last = sheet.getLastRow();
  if (last < 2) return false;
  var values = sheet.getRange(2, EMAIL_COL, last, EMAIL_COL).getValues();
  for (var i = 0; i < values.length; i++) {
    var cell = String(values[i][0] || "")
      .trim()
      .toLowerCase();
    if (cell && cell === email) return true;
  }
  return false;
}

function sendThankYou_(name, email) {
  var greeting = name ? "Hi " + name + "," : "Hi,";
  var subject = "Thanks for joining the AppReviewr App Store waitlist";
  var body =
    greeting +
    "\n\n" +
    "Thank you for joining the AppReviewr waitlist for App Store review export. " +
    "We really appreciate your interest — Google Play export is live today, and " +
    "App Store support is next.\n\n" +
    "If you have feature ideas (filters, countries, formats, workflows), just reply " +
    "to this email. Your suggestions help us prioritize what to build.\n\n" +
    "We'll email you again when App Store export ships.\n\n" +
    "— The AppReviewr team\n";

  GmailApp.sendEmail(email, subject, body);
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON,
  );
}
```

3. **Save**.

## 3. Deploy (and allow Gmail)

1. **Deploy → New deployment** → type **Web app**.
2. **Execute as:** Me · **Who has access:** Anyone → **Deploy**.
3. Authorize when prompted — approve **Gmail** / send email scopes (required for thank-you mail).
4. Copy the `/exec` URL.

> After updating the script: **Deploy → Manage deployments → Edit → New version → Deploy**.

**Mail note:** Emails send from the Google account that owns the deployment (“Execute as Me”). That account must be allowed to send mail (normal consumer/Workspace Gmail). First-run authorization must include Gmail permission; if thank-you mail fails, check Apps Script **Executions** logs and re-authorize.

## 4. Wire AppReviewr env

`frontend/.env.local` (and production):

```bash
APPS_SCRIPT_WAITLIST_URL=https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec

# Shown in footer + “Suggest a feature” mailto (optional until set)
NEXT_PUBLIC_SUPPORT_EMAIL=hello@yourdomain.com
```

Rebuild / restart the frontend after changes.

## 5. Test

1. Submit once → Sheet row + thank-you email + UI “You're on the list”.
2. Submit same email again (or clear only the form without clearing localStorage) → `{ already: true }`, no second row / no second thank-you.
3. Clear `localStorage` key `appreviewr-app-store-waitlist-joined` and resubmit same email → still no duplicate row (`already: true`).
