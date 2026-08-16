const state = {
  posts: [],
  selectedId: null,
  installMode: window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true
};

const elements = {
  connection: document.querySelector("#connection-status"),
  loginCard: document.querySelector("#login-card"),
  loginForm: document.querySelector("#login-form"),
  loginButton: document.querySelector("#login-button"),
  accessKey: document.querySelector("#access-key"),
  protectedSections: [...document.querySelectorAll(".protected")],
  logoutButton: document.querySelector("#logout-button"),
  installCard: document.querySelector("#install-card"),
  notificationButton: document.querySelector("#notification-button"),
  notificationTitle: document.querySelector("#notification-title"),
  notificationCopy: document.querySelector("#notification-copy"),
  selectedDay: document.querySelector("#selected-day"),
  selectedTime: document.querySelector("#selected-time"),
  selectedTitle: document.querySelector("#selected-title"),
  selectedReadiness: document.querySelector("#selected-readiness"),
  mediaFrame: document.querySelector("#media-frame"),
  postCopy: document.querySelector("#post-copy"),
  characterCount: document.querySelector("#character-count"),
  resetCopy: document.querySelector("#reset-copy"),
  notes: document.querySelector("#notes"),
  notesList: document.querySelector("#notes-list"),
  postButton: document.querySelector("#post-button"),
  copyButton: document.querySelector("#copy-button"),
  thread: document.querySelector("#thread"),
  replyCount: document.querySelector("#reply-count"),
  replyList: document.querySelector("#reply-list"),
  queue: document.querySelector("#queue"),
  toast: document.querySelector("#toast")
};

function showLogin() {
  elements.loginCard.hidden = false;
  elements.protectedSections.forEach((section) => {
    section.hidden = true;
  });
  elements.accessKey.focus();
}

function showApp() {
  elements.loginCard.hidden = true;
  elements.protectedSections.forEach((section) => {
    section.hidden = section === elements.installCard;
  });
}

function toast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => elements.toast.classList.remove("visible"), 2800);
}

function editedKey(id) {
  return `termfetch-copy:${id}`;
}

function getPostCopy(post) {
  return localStorage.getItem(editedKey(post.id)) ?? post.body;
}

function formatTime(value) {
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

function readinessLabel(value) {
  return {
    ready: "READY",
    "needs-edit": "EDIT NEEDED",
    "needs-media": "MEDIA NEEDED",
    "native-poll": "ADD POLL"
  }[value] || "REVIEW";
}

function selectedPost() {
  return state.posts.find((post) => post.id === state.selectedId) || state.posts[0];
}

function setSelected(id, updateUrl = true) {
  state.selectedId = id;
  if (updateUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set("post", id);
    history.replaceState({}, "", url);
  }
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderMedia(post) {
  elements.mediaFrame.replaceChildren();
  if (!post.media) {
    elements.mediaFrame.hidden = true;
    return;
  }
  const media = post.media.type.startsWith("video/")
    ? document.createElement("video")
    : document.createElement("img");
  media.src = post.media.url;
  media.setAttribute("playsinline", "");
  if (media.tagName === "VIDEO") {
    media.controls = true;
    media.muted = true;
    media.loop = true;
  } else {
    media.alt = `${post.title} preview`;
  }
  elements.mediaFrame.append(media);
  elements.mediaFrame.hidden = false;
}

function renderReplies(post) {
  elements.replyList.replaceChildren();
  if (!post.replies.length) {
    elements.thread.hidden = true;
    return;
  }
  elements.thread.hidden = false;
  elements.replyCount.textContent = `${post.replies.length} prepared`;
  post.replies.forEach((reply, index) => {
    const card = document.createElement("div");
    card.className = "reply-card";
    card.textContent = reply;
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-label", `Copy reply ${index + 1}`);
    button.textContent = "⧉";
    button.addEventListener("click", async () => {
      await navigator.clipboard.writeText(reply);
      toast(`Reply ${index + 1} copied`);
    });
    card.append(button);
    elements.replyList.append(card);
  });
}

function renderQueue() {
  elements.queue.replaceChildren();
  state.posts.forEach((post) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `queue-item${post.id === state.selectedId ? " selected" : ""}`;
    button.addEventListener("click", () => setSelected(post.id));

    const day = document.createElement("span");
    day.className = "queue-day";
    day.textContent = `D${post.day}`;
    const copy = document.createElement("span");
    copy.className = "queue-copy";
    const title = document.createElement("strong");
    title.textContent = post.title;
    const time = document.createElement("span");
    time.textContent = formatTime(post.scheduledAt);
    copy.append(title, time);
    const status = document.createElement("span");
    status.className = "queue-state";
    status.textContent = post.readiness === "ready" ? "●" : "○";
    status.title = readinessLabel(post.readiness);
    button.append(day, copy, status);
    elements.queue.append(button);
  });
}

function render() {
  const post = selectedPost();
  if (!post) return;
  const copy = getPostCopy(post);
  elements.selectedDay.textContent = `DAY ${post.day}`;
  elements.selectedTime.textContent = `${formatTime(post.scheduledAt)} IST`;
  elements.selectedTitle.textContent = post.title;
  elements.selectedReadiness.textContent = readinessLabel(post.readiness);
  elements.selectedReadiness.classList.toggle("warning", post.readiness !== "ready");
  elements.postCopy.value = copy;
  elements.characterCount.textContent = `${copy.length} characters`;

  elements.notesList.replaceChildren();
  post.notes.forEach((note) => {
    const item = document.createElement("li");
    item.textContent = note;
    elements.notesList.append(item);
  });
  elements.notes.hidden = post.notes.length === 0;
  renderMedia(post);
  renderReplies(post);
  renderQueue();
}

function base64UrlToBytes(value) {
  const padded = value + "=".repeat((4 - (value.length % 4)) % 4);
  const binary = atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

async function currentSubscription() {
  if (!("serviceWorker" in navigator)) return null;
  const registration = await navigator.serviceWorker.ready;
  return registration.pushManager.getSubscription();
}

async function updateNotificationState() {
  elements.installCard.hidden = true;
  if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
    elements.notificationButton.disabled = true;
    elements.notificationTitle.textContent = "Notifications unavailable";
    elements.notificationCopy.textContent = "This browser does not support web notifications.";
    return;
  }
  if (!state.installMode && /iPhone|iPad|iPod/.test(navigator.userAgent)) {
    elements.installCard.hidden = false;
    elements.notificationButton.disabled = true;
    elements.notificationCopy.textContent = "Install this page on your Home Screen first.";
    return;
  }
  const subscription = await currentSubscription();
  if (subscription) {
    elements.notificationButton.textContent = "Send test";
    elements.notificationTitle.textContent = "Notifications enabled";
    elements.notificationCopy.textContent = "You’ll be alerted when each post is ready.";
  }
}

async function enableOrTestNotifications() {
  elements.notificationButton.disabled = true;
  try {
    let subscription = await currentSubscription();
    if (!subscription) {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") throw new Error("Notification permission was not granted");
      const configResponse = await fetch("/api/config");
      if (!configResponse.ok) throw new Error("Could not load notification settings");
      const { vapidPublicKey } = await configResponse.json();
      if (!vapidPublicKey) throw new Error("Notifications are not configured yet");
      const registration = await navigator.serviceWorker.ready;
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: base64UrlToBytes(vapidPublicKey)
      });
      const saveResponse = await fetch("/api/subscriptions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(subscription.toJSON())
      });
      if (!saveResponse.ok) throw new Error("Could not save the notification subscription");
    }
    const testResponse = await fetch("/api/test-notification", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ endpoint: subscription.endpoint })
    });
    if (!testResponse.ok) {
      const details = await testResponse.json().catch(() => ({}));
      throw new Error(details.error || "Could not send the test notification");
    }
    toast("Test notification sent");
    await updateNotificationState();
  } catch (error) {
    toast(error.message || "Could not enable notifications");
  } finally {
    elements.notificationButton.disabled = false;
  }
}

async function copyText() {
  await navigator.clipboard.writeText(elements.postCopy.value);
  toast("Post text copied");
}

async function mediaFile(post) {
  if (!post.media) return null;
  const response = await fetch(post.media.url);
  if (!response.ok) throw new Error("Could not download the launch media");
  const blob = await response.blob();
  return new File([blob], post.media.filename, { type: post.media.type });
}

function xIntent(text) {
  return `https://x.com/intent/post?text=${encodeURIComponent(text)}`;
}

async function postOnX() {
  const post = selectedPost();
  const text = elements.postCopy.value.trim();
  if (!text) {
    toast("Add post text first");
    return;
  }
  elements.postButton.disabled = true;
  elements.postButton.textContent = "Preparing…";
  try {
    if (post.media && navigator.share) {
      const file = await mediaFile(post);
      const shareData = { text, files: [file] };
      if (!navigator.canShare || navigator.canShare(shareData)) {
        await navigator.share(shareData);
        toast("Shared to your iPhone share sheet");
        return;
      }
    }
    await navigator.clipboard.writeText(text);
    window.location.href = xIntent(text);
  } catch (error) {
    if (error.name !== "AbortError") {
      await navigator.clipboard.writeText(text).catch(() => {});
      window.location.href = xIntent(text);
    }
  } finally {
    elements.postButton.disabled = false;
    elements.postButton.textContent = "Post on X";
  }
}

async function loadQueue() {
  try {
    const response = await fetch("/api/posts");
    if (response.status === 401) {
      showLogin();
      return;
    }
    if (!response.ok) throw new Error("Could not load posts");
    const payload = await response.json();
    state.posts = payload.posts;
    const requested = new URL(window.location.href).searchParams.get("post");
    const upcoming = state.posts.find((post) => Date.parse(post.scheduledAt) >= Date.now());
    state.selectedId = state.posts.some((post) => post.id === requested)
      ? requested
      : (upcoming || state.posts.at(-1)).id;
    elements.connection.classList.add("online");
    elements.connection.setAttribute("aria-label", "Connected");
    showApp();
    render();
    await updateNotificationState();
  } catch (error) {
    elements.selectedTitle.textContent = "The launch queue could not load";
    toast(error.message || "Connection failed");
  }
}

async function login(event) {
  event.preventDefault();
  elements.loginButton.disabled = true;
  elements.loginButton.textContent = "Unlocking…";
  try {
    const response = await fetch("/api/session", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ accessKey: elements.accessKey.value.trim() })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "Could not unlock the queue");
    elements.accessKey.value = "";
    await loadQueue();
    toast("Private queue unlocked");
  } catch (error) {
    toast(error.message || "Could not unlock the queue");
  } finally {
    elements.loginButton.disabled = false;
    elements.loginButton.textContent = "Unlock queue";
  }
}

async function logout() {
  await fetch("/api/session", { method: "DELETE" });
  state.posts = [];
  showLogin();
  toast("App locked");
}

async function initialise() {
  if ("serviceWorker" in navigator) await navigator.serviceWorker.register("/sw.js");
  const session = await fetch("/api/session");
  if (!session.ok) {
    showLogin();
    return;
  }
  await loadQueue();
}

elements.notificationButton.addEventListener("click", enableOrTestNotifications);
elements.loginForm.addEventListener("submit", login);
elements.logoutButton.addEventListener("click", logout);
elements.postCopy.addEventListener("input", () => {
  const post = selectedPost();
  localStorage.setItem(editedKey(post.id), elements.postCopy.value);
  elements.characterCount.textContent = `${elements.postCopy.value.length} characters`;
});
elements.resetCopy.addEventListener("click", () => {
  const post = selectedPost();
  localStorage.removeItem(editedKey(post.id));
  render();
  toast("Original copy restored");
});
elements.copyButton.addEventListener("click", copyText);
elements.postButton.addEventListener("click", postOnX);

initialise();
