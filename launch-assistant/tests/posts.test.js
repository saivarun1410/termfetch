import test from "node:test";
import assert from "node:assert/strict";
import { POSTS, duePosts, findPost } from "../src/posts.js";
import { constantTimeEqual, validSubscription } from "../src/worker.js";

test("launch queue contains seven ordered daily posts", () => {
  assert.equal(POSTS.length, 7);
  assert.deepEqual(POSTS.map((post) => post.day), [1, 2, 3, 4, 5, 6, 7]);
  for (let index = 1; index < POSTS.length; index += 1) {
    assert.ok(Date.parse(POSTS[index].scheduledAt) > Date.parse(POSTS[index - 1].scheduledAt));
  }
});

test("launch post is ready and carries the demo video", () => {
  const launch = findPost("launch");
  assert.equal(launch.readiness, "ready");
  assert.equal(launch.media.type, "video/mp4");
  assert.match(launch.body, /github\.com\/saivarun1410\/termfetch/);
});

test("duePosts only returns posts inside the delivery window", () => {
  const fiveMinutesAfterLaunch = new Date("2026-08-18T15:35:00.000Z");
  assert.deepEqual(duePosts(fiveMinutesAfterLaunch).map((post) => post.id), ["launch"]);
  assert.deepEqual(duePosts(new Date("2026-08-19T14:00:00.000Z")), []);
});

test("subscription validation rejects insecure or incomplete endpoints", () => {
  const valid = {
    endpoint: "https://web.push.apple.com/example",
    keys: { p256dh: "public-key", auth: "auth-key" }
  };
  assert.equal(validSubscription(valid), true);
  assert.equal(validSubscription({ ...valid, endpoint: "http://example.com" }), false);
  assert.equal(validSubscription({ endpoint: valid.endpoint, keys: {} }), false);
});

test("owner access comparison rejects mismatches without prefix shortcuts", () => {
  assert.equal(constantTimeEqual("private-key", "private-key"), true);
  assert.equal(constantTimeEqual("private-key", "private"), false);
  assert.equal(constantTimeEqual("private-key", "private-keY"), false);
  assert.equal(constantTimeEqual(null, "private-key"), false);
});
