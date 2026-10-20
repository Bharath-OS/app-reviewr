# App Store waitlist → Google Apps Script → Sheet

Yes — **Apps Script → Sheet is better** than posting to a Google Form `formResponse` URL from the browser:

- Real JSON success/error (no hidden iframe / opaque CORS)
- Deploy URL stays **server-side** (`APPS_SCRIPT_WAITLIST_URL`) so it is not shipped to visitors
- Optional “why do you need this?” field is a normal column

Flow: browser → `POST /api/waitlist` (Next.js) → Apps Script web app → append row to Sheet.

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

3. **Save** (disk icon) and name the project e.g. `AppReviewr Waitlist`.

## 3. Deploy as a web app

1. Click **Deploy → New deployment**.
2. Gear icon → type **Web app**.
3. Settings:
   - **Description:** `waitlist v1`
   - **Execute as:** **Me**
   - **Who has access:** **Anyone**
4. **Deploy**.
5. Authorize the script when prompted (choose your Google account → Advanced → Go to … → Allow).
6. Copy the **Web app URL**  
   (`https://script.google.com/macros/s/…/exec`).

> After editing the script later: **Deploy → Manage deployments → Edit → New version → Deploy**, then keep using the same URL (or copy the new one if you created a fresh deployment).

## 4. Wire AppReviewr

In `frontend/.env.local` (and production host env):

```bash
APPS_SCRIPT_WAITLIST_URL=https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec
```

**Important:** this is a **server** env var (no `NEXT_PUBLIC_`). The Next.js route `POST /api/waitlist` reads it and forwards JSON `{ name, email, message }` so browsers never see the Script URL.

Restart / rebuild the frontend:

```bash
cd frontend
npm run build
npm run start
# or: npm run dev
```

## 5. Test

1. Open `/app-store-waitlist`.
2. Submit Name + Email (+ optional need).
3. Confirm a new row in the Sheet.
4. `GET /api/waitlist` should return `{ "configured": true, … }`.

## Security notes

- **Anyone** can call the web app URL if they obtain it — keep it server-side only.
- The Next.js handler validates email format and field length before forwarding.
- For higher volume, add a shared secret header checked in `doPost` and sent from `/api/waitlist`.

## Deprecated (removed from UI)

The older Google Form `formResponse` + `entry.*` / hidden-iframe approach is no longer used. Prefer this Apps Script path.
