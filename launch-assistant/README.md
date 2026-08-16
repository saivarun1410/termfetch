# Termfetch Launch Assistant

An installable iPhone web app that turns the seven-day Termfetch launch plan
into a private approval queue. It sends a Web Push notification when a post is
ready, shows the final copy and media, and hands the approved content to X. The
user always performs the final publish action.

## What it does

- Schedules the seven launch reminders for 9:00 PM IST.
- Installs as a Home Screen app on iOS 16.4 or newer.
- Sends a test notification immediately after enrollment.
- Shows launch media, editable copy, readiness warnings, and prepared replies.
- Uses the iPhone share sheet for media posts and an X Web Intent fallback.
- Stores edits only on the device. It does not collect X credentials.
- Protects the queue and all APIs with an owner-only access key and secure,
  HTTP-only session cookie.

## Cloudflare setup

1. Install dependencies with `npm install`.
2. Generate a VAPID key pair and set the public key in `wrangler.jsonc`.
3. Create the D1 database, replace its ID in `wrangler.jsonc`, and apply
   `schema.sql` remotely.
4. Store the private VAPID key with
   `npx wrangler secret put VAPID_PRIVATE_KEY`.
5. Store strong `APP_ACCESS_KEY` and `SESSION_SECRET` values as Worker secrets.
6. Run `npm run build`, then `npm run deploy`.

The Cloudflare Worker serves the PWA, stores browser push subscriptions in D1,
and checks the launch queue once per minute. A notification is marked sent only
after at least one push service accepts it.

## iPhone setup

Open the deployed URL in Safari, tap **Share → Add to Home Screen**, open the
new icon, and tap **Enable**. iOS asks for notification permission and the app
sends a test notification.

## Safety

This assistant cannot publish silently and never receives an X password or API
token. Placeholder community names, screenshots, and week-one metrics remain
blocked for explicit editing.
