"use strict";

// Performs Arctic Shift requests on behalf of the content scripts. They can't
// fetch the archive themselves in Firefox: MV3 content-script requests run
// with the page's principal there, so Reddit's CSP (whose connect-src doesn't
// list the archive) blocks them — and hands each blocked URL, username
// included, to Reddit's page as a CSP violation. The background isn't subject
// to the page's CSP, and the host permission covers the cross-origin request
// in every browser.

const extensionApi = globalThis.browser ?? globalThis.chrome;

const API_BASE = "https://arctic-shift.photon-reddit.com/api";
const REQUEST_TIMEOUT_MS = 20000;
// The endpoints the content scripts use; nothing else is fetched on request.
const ALLOWED_PATHS = new Set(["/posts/search", "/comments/search", "/posts/ids", "/comments/ids"]);

async function timedFetch(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function doFetch(path, params) {
  const url = new URL(`${API_BASE}${path}`);
  for (const [k, v] of Object.entries(params || {})) {
    if (v === undefined || v === null || v === "") continue;
    url.searchParams.set(k, String(v));
  }
  const resp = await timedFetch(url.toString(), {
    headers: { Accept: "application/json" },
  });
  if (!resp.ok) {
    throw new Error(`Arctic Shift HTTP ${resp.status} for ${path}`);
  }
  const json = await resp.json();
  return json && Array.isArray(json.data) ? json.data : [];
}

// Replies via sendResponse + `return true` rather than a returned promise:
// that's the async form both Chrome and Firefox accept.
extensionApi.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "arctic-shift") return false;
  if (!ALLOWED_PATHS.has(message.path)) {
    sendResponse({ error: `Unsupported Arctic Shift path ${message.path}` });
    return false;
  }
  doFetch(message.path, message.params).then(
    (data) => sendResponse({ data }),
    (err) => sendResponse({ error: err && err.message ? err.message : String(err) })
  );
  return true;
});
