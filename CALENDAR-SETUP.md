# Connect the website calendar to joe@vincerelegalmarketing.com

The booking calendar on the site is already built. Once these steps are done, it:
- hides any time you are busy in Google Calendar
- puts each booking straight on your calendar, with a Google Meet link
- has Google email the client an invite

Until then, bookings still reach you by email, and the site tells the client you will confirm by email.

Allow about 15 minutes. You need to be an admin of the vincerelegalmarketing.com Google Workspace.

## 1. Create a Google Cloud project and turn on the Calendar API

1. Go to https://console.cloud.google.com and sign in as joe@vincerelegalmarketing.com.
2. Use the project picker at the top: **New project**, name it `Vincere website`, then **Create**. Make sure it is selected.
3. Go to **APIs & Services → Library**, search for **Google Calendar API**, open it, and click **Enable**.

## 2. Create the service account (the website's robot login)

1. Go to **IAM & Admin → Service accounts → Create service account**.
2. Name it `vincere-booking`. Click **Create and continue**, skip the roles, then **Done**.
3. Click the new service account. On the **Details** tab, copy the **Unique ID** (a long number). You need it in step 3.
4. Open the **Keys** tab and choose **Add key → Create new key → JSON → Create**. A `.json` file downloads.
   - If Google says key creation is disabled by an organization policy, go to **IAM & Admin → Organization policies**, find **Disable service account key creation**, and set it to **Off** for this project. Then try again.
5. Keep the JSON file private. Do not email it, paste it into chat or commit it anywhere.

## 3. Let the service account manage your calendar (domain-wide delegation)

1. Go to https://admin.google.com, then **Security → Access and data control → API controls**.
2. Click **Manage domain wide delegation**, then **Add new**.
3. **Client ID**: paste the Unique ID from step 2.3.
4. **OAuth scopes**: `https://www.googleapis.com/auth/calendar`
5. Click **Authorize**.

## 4. Add the key to Netlify

1. Open the site in Netlify, then **Site configuration → Environment variables → Add a variable**.
2. Add these two variables. For each one, make sure the scope includes **Functions**.

| Key | Value (from the JSON file) |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_EMAIL` | the `client_email` value, e.g. `vincere-booking@vincere-website.iam.gserviceaccount.com` |
| `GOOGLE_PRIVATE_KEY` | the whole `private_key` value, from `-----BEGIN PRIVATE KEY-----` through `-----END PRIVATE KEY-----\n`. Paste it exactly as it appears, `\n` characters included. |

3. Optional: `CALENDAR_USER` is only needed if bookings should go to a calendar other than joe@vincerelegalmarketing.com.
4. Go to **Deploys → Trigger deploy → Deploy site** so the function picks up the new variables.

## 5. Test it

1. Add a test event to your Google Calendar during your booking hours, for example next Monday 9:00–10:00 AM ET.
2. Open https://vincerelegalmarketing.com/#contact and pick that Monday. The 9:00 and 9:30 slots should be gone.
3. Book another slot with a personal email address. Check that:
   - the event appears on your calendar, with a Meet link
   - the personal address gets the Google invite
   - the Netlify form email says **Added to Google Calendar, invite sent**
4. Delete the test events.

If the form email says **Not added to calendar**, open Netlify, go to **Logs → Functions → calendar**, and send the error line to Claude.

## Booking hours

The hours are US Eastern, in 30-minute slots. Each visitor sees them in their own time zone.

| Day | Hours (ET) |
|---|---|
| Monday | 9:00 AM – 1:00 PM |
| Tuesday | 10:00 – 11:30 AM |
| Wednesday | 9:00 AM – 1:00 PM |
| Thursday | 3:00 PM – 7:00 PM |
| Friday | 9:00 AM – 1:00 PM and 3:00 PM – 7:00 PM |

The times listed are start times, so the last calls start at 1:00 PM and 7:00 PM. To change the hours, edit `HOURS` in two files and keep them identical:
- `build/booking.js` in the claudejoey repo
- `netlify/functions/calendar.js` in the vincere-site repo
