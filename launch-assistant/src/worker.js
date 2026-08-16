import { buildPushPayload } from "@block65/webcrypto-web-push";
import { duePosts, findPost, publicPosts } from "./posts.js";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store"
};

const SESSION_COOKIE = "__Host-termfetch_session";
const SESSION_MAX_AGE = 60 * 60 * 24 * 30;

function json(data, init = {}) {
  return new Response(JSON.stringify(data), {
    ...init,
    headers: { ...JSON_HEADERS, ...(init.headers || {}) }
  });
}

function validSubscription(value) {
  if (!value || typeof value !== "object") return false;
  if (typeof value.endpoint !== "string" || value.endpoint.length > 2048) return false;
  try {
    const endpoint = new URL(value.endpoint);
    if (endpoint.protocol !== "https:") return false;
  } catch {
    return false;
  }
  return Boolean(
    value.keys &&
      typeof value.keys.p256dh === "string" &&
      value.keys.p256dh.length < 512 &&
      typeof value.keys.auth === "string" &&
      value.keys.auth.length < 512
  );
}

async function readJson(request) {
  const type = request.headers.get("content-type") || "";
  if (!type.includes("application/json")) throw new Error("Expected JSON");
  return request.json();
}

function constantTimeEqual(left, right) {
  if (typeof left !== "string" || typeof right !== "string") return false;
  const length = Math.max(left.length, right.length);
  let difference = left.length ^ right.length;
  for (let index = 0; index < length; index += 1) {
    difference |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
  }
  return difference === 0;
}

function cookieValue(request, name) {
  const cookies = request.headers.get("cookie") || "";
  for (const entry of cookies.split(";")) {
    const [key, ...parts] = entry.trim().split("=");
    if (key === name) return parts.join("=");
  }
  return "";
}

async function sessionToken(env) {
  if (!env.APP_ACCESS_KEY || !env.SESSION_SECRET) {
    throw new Error("Owner authentication is not configured");
  }
  const input = new TextEncoder().encode(
    `termfetch-launch:${env.APP_ACCESS_KEY}:${env.SESSION_SECRET}`
  );
  const digest = await crypto.subtle.digest("SHA-256", input);
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

async function isAuthorized(request, env) {
  const received = cookieValue(request, SESSION_COOKIE);
  if (!received) return false;
  return constantTimeEqual(received, await sessionToken(env));
}

function vapid(env) {
  if (!env.VAPID_PUBLIC_KEY || !env.VAPID_PRIVATE_KEY || !env.VAPID_SUBJECT) {
    throw new Error("Push notification keys are not configured");
  }
  return {
    subject: env.VAPID_SUBJECT,
    publicKey: env.VAPID_PUBLIC_KEY,
    privateKey: env.VAPID_PRIVATE_KEY
  };
}

async function sendPush(subscription, message, env) {
  const payload = await buildPushPayload(
    { data: JSON.stringify(message), options: { ttl: 60 * 60 * 6 } },
    subscription,
    vapid(env)
  );
  return fetch(subscription.endpoint, payload);
}

async function removeSubscription(env, endpoint) {
  await env.DB.prepare("DELETE FROM push_subscriptions WHERE endpoint = ?")
    .bind(endpoint)
    .run();
}

async function handleApi(request, env, url) {
  if (url.pathname === "/api/session" && request.method === "POST") {
    let body;
    try {
      body = await readJson(request);
    } catch {
      return json({ error: "Invalid login" }, { status: 400 });
    }
    if (!constantTimeEqual(body?.accessKey, env.APP_ACCESS_KEY)) {
      return json({ error: "That access key is not valid" }, { status: 401 });
    }
    return json(
      { ok: true },
      {
        headers: {
          "set-cookie": `${SESSION_COOKIE}=${await sessionToken(env)}; Path=/; Max-Age=${SESSION_MAX_AGE}; Secure; HttpOnly; SameSite=Strict`
        }
      }
    );
  }

  if (url.pathname === "/api/session" && request.method === "GET") {
    const authenticated = await isAuthorized(request, env);
    return json({ authenticated }, { status: authenticated ? 200 : 401 });
  }

  if (url.pathname === "/api/session" && request.method === "DELETE") {
    return json(
      { ok: true },
      {
        headers: {
          "set-cookie": `${SESSION_COOKIE}=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Strict`
        }
      }
    );
  }

  if (!(await isAuthorized(request, env))) {
    return json({ error: "Authentication required" }, { status: 401 });
  }

  if (request.method === "GET" && url.pathname === "/api/config") {
    return json({ vapidPublicKey: env.VAPID_PUBLIC_KEY || "" });
  }

  if (request.method === "GET" && url.pathname === "/api/posts") {
    return json({ posts: publicPosts(), serverTime: new Date().toISOString() });
  }

  if (request.method === "POST" && url.pathname === "/api/subscriptions") {
    let subscription;
    try {
      subscription = await readJson(request);
    } catch {
      return json({ error: "Invalid subscription" }, { status: 400 });
    }
    if (!validSubscription(subscription)) {
      return json({ error: "Invalid subscription" }, { status: 400 });
    }
    await env.DB.prepare(
      `INSERT INTO push_subscriptions (endpoint, expiration_time, p256dh, auth)
       VALUES (?, ?, ?, ?)
       ON CONFLICT(endpoint) DO UPDATE SET
         expiration_time = excluded.expiration_time,
         p256dh = excluded.p256dh,
         auth = excluded.auth`
    )
      .bind(
        subscription.endpoint,
        subscription.expirationTime ?? null,
        subscription.keys.p256dh,
        subscription.keys.auth
      )
      .run();
    return json({ ok: true }, { status: 201 });
  }

  if (request.method === "DELETE" && url.pathname === "/api/subscriptions") {
    let subscription;
    try {
      subscription = await readJson(request);
    } catch {
      return json({ error: "Invalid subscription" }, { status: 400 });
    }
    if (typeof subscription?.endpoint !== "string") {
      return json({ error: "Invalid subscription" }, { status: 400 });
    }
    await removeSubscription(env, subscription.endpoint);
    return json({ ok: true });
  }

  if (request.method === "POST" && url.pathname === "/api/test-notification") {
    let body;
    try {
      body = await readJson(request);
    } catch {
      return json({ error: "Invalid request" }, { status: 400 });
    }
    if (typeof body?.endpoint !== "string") {
      return json({ error: "Unknown subscription" }, { status: 404 });
    }
    const record = await env.DB.prepare(
      `SELECT endpoint, expiration_time, p256dh, auth, last_test_at
       FROM push_subscriptions WHERE endpoint = ?`
    )
      .bind(body.endpoint)
      .first();
    if (!record) return json({ error: "Unknown subscription" }, { status: 404 });
    if (record.last_test_at && Date.now() - Date.parse(record.last_test_at) < 60_000) {
      return json({ error: "Please wait before sending another test" }, { status: 429 });
    }
    const response = await sendPush(
      {
        endpoint: record.endpoint,
        expirationTime: record.expiration_time,
        keys: { p256dh: record.p256dh, auth: record.auth }
      },
      {
        title: "Termfetch Launch",
        body: "Notifications are ready. Tap to preview the launch post.",
        tag: "termfetch-test",
        postId: "launch",
        url: "/?post=launch"
      },
      env
    );
    if (response.status === 404 || response.status === 410) {
      await removeSubscription(env, record.endpoint);
    }
    if (!response.ok) return json({ error: "Push service rejected the notification" }, { status: 502 });
    await env.DB.prepare(
      "UPDATE push_subscriptions SET last_test_at = CURRENT_TIMESTAMP WHERE endpoint = ?"
    )
      .bind(record.endpoint)
      .run();
    return json({ ok: true });
  }

  return json({ error: "Not found" }, { status: 404 });
}

function withSecurityHeaders(response, origin) {
  let next = new Response(response.body, response);
  if ((next.headers.get("content-type") || "").includes("text/html")) {
    next = new HTMLRewriter()
      .on('meta[property="og:image"], meta[name="twitter:image"]', {
        element(element) {
          element.setAttribute("content", `${origin}/og.png`);
        }
      })
      .transform(next);
  }
  next.headers.set("x-content-type-options", "nosniff");
  next.headers.set("referrer-policy", "no-referrer");
  next.headers.set("permissions-policy", "camera=(), microphone=(), geolocation=()");
  next.headers.set("x-frame-options", "DENY");
  next.headers.set(
    "content-security-policy",
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https://raw.githubusercontent.com; media-src 'self' https://raw.githubusercontent.com; connect-src 'self' https://raw.githubusercontent.com; manifest-src 'self'; worker-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
  );
  return next;
}

async function notifyDuePosts(env) {
  const subscriptions = await env.DB.prepare(
    "SELECT endpoint, expiration_time, p256dh, auth FROM push_subscriptions"
  ).all();
  if (!subscriptions.results.length) return;

  for (const post of duePosts()) {
    const alreadySent = await env.DB.prepare(
      "SELECT post_id FROM sent_notifications WHERE post_id = ?"
    )
      .bind(post.id)
      .first();
    if (alreadySent) continue;

    let delivered = 0;
    for (const record of subscriptions.results) {
      const subscription = {
        endpoint: record.endpoint,
        expirationTime: record.expiration_time,
        keys: { p256dh: record.p256dh, auth: record.auth }
      };
      try {
        const response = await sendPush(
          subscription,
          {
            title: post.readiness === "ready" ? "Ready to post" : "Needs your review",
            body: `Day ${post.day}: ${post.title}`,
            tag: `termfetch-${post.id}`,
            postId: post.id,
            url: `/?post=${encodeURIComponent(post.id)}`
          },
          env
        );
        if (response.ok) delivered += 1;
        if (response.status === 404 || response.status === 410) {
          await removeSubscription(env, record.endpoint);
        }
      } catch (error) {
        console.error("Push delivery failed", post.id, error);
      }
    }
    if (delivered > 0) {
      await env.DB.prepare(
        "INSERT OR IGNORE INTO sent_notifications (post_id, recipient_count) VALUES (?, ?)"
      )
        .bind(post.id, delivered)
        .run();
    }
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      try {
        return await handleApi(request, env, url);
      } catch (error) {
        console.error("API error", error);
        return json({ error: "Something went wrong" }, { status: 500 });
      }
    }
    return withSecurityHeaders(await env.ASSETS.fetch(request), url.origin);
  },

  async scheduled(_controller, env, context) {
    context.waitUntil(notifyDuePosts(env));
  }
};

export { constantTimeEqual, validSubscription, notifyDuePosts };
