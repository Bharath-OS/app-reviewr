# App Store waitlist → Google Apps Script → Sheet

Browser → `POST /api/waitlist` (Next.js) → Apps Script web app → append row to a Google Sheet.

The Script deploy URL stays **server-side** (`APPS_SCRIPT_WAITLIST_URL`) so it is not shipped to visitors.

## 1. Create a Google Sheet

1. Open [Google Sheets](https://sheets.google.com) → **Blank spreadsheet**.
2. Rename it e.g. `AppReviewr App Store Waitlist`.
3. On the first tab, set headers in row 1:

| A | B | C | D |
|---|---|---|---|
| Timestamp | Name | Email | Need |

4. Rename the tab to `Waitlist` (must match the script below).

## 2. Paste the Apps Script

1. In the Sheet: **Extensions → Apps Script**.
2. Delete any stub code and paste:

```javascript
/**
 * AppReviewr waitlist receiver.
 * Deploy as Web app → Execute as: Me → Who has access: Anyone
 */
var SHEET_NAME = "Waitlist";

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || "{}";
    var data = JSON.parse(raw);
    var name = String(data.name || "").trim();
    var email = String(data.email || "").trim();
    var message = String(data.message || "").trim();

    if (!email) {
      return json_({ ok: false, error: "Email is required." });
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME);
      sheet.appendRow(["Timestamp", "Name", "Email", "Need"]);
    }

    sheet.appendRow([new Date(), name, email, message]);
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function doGet() {
  return json_({ ok: true, service: "AppReviewr waitlist" });
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON,
  );
}
```

3. **Save** and name the project e.g. `AppReviewr Waitlist`.

## 3. Deploy as a web app

1. Click **Deploy → New deployment**.
2. Gear icon → type **Web app**.
3. Settings:
   - **Description:** `waitlist v1`
   - **Execute as:** **Me**
   - **Who has access:** **Anyone**
4. **Deploy**.
5. Authorize when prompted.
6. Copy the **Web app URL** (`https://script.google.com/macros/s/…/exec`).

> After editing the script later: **Deploy → Manage deployments → Edit → New version → Deploy**.

## 4. Wire AppReviewr

In `frontend/.env.local` (and production host env):

```bash
APPS_SCRIPT_WAITLIST_URL=https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec
```

This is a **server** env var (no `NEXT_PUBLIC_`). Restart / rebuild the frontend after setting it.

## 5. Test

1. Open `/app-store-waitlist` and submit Name + Email (+ optional need).
2. Confirm a new row in the Sheet.
3. `GET /api/waitlist` should return `{ "configured": true, … }`.

## Security notes

- Keep the web app URL server-side only.
- The Next.js handler validates email format and field length before forwarding.
- For higher volume, add a shared secret header checked in `doPost`.
