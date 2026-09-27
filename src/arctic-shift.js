"use strict";

(function () {
  const extensionApi = globalThis.browser ?? globalThis.chrome;
  const MAX_CACHE_ENTRIES = 50;

  const cache = new Map();

  function cacheKey(path, params) {
    const parts = Object.keys(params)
      .sort()
      .map((k) => `${k}=${params[k]}`)
      .join("&");
    return `${path}?${parts}`;
  }

  function cacheGet(key) {
    if (!cache.has(key)) return undefined;
    const value = cache.get(key);
    cache.delete(key);
    cache.set(key, value);
    return value;
  }

  function cachePut(key, value) {
    if (cache.has(key)) cache.delete(key);
    cache.set(key, value);
    while (cache.size > MAX_CACHE_ENTRIES) {
      cache.delete(cache.keys().next().value);
    }
  }

  // A message can reach Firefox's idle event page just as it's being torn
  // down, failing with "Receiving end does not exist". The next message wakes
  // a fresh background, so a failed send gets one retry. (Archive errors come
  // back as reply.error and aren't retried.)
  async function sendToBackground(message) {
    try {
      return await extensionApi.runtime.sendMessage(message);
    } catch {
      return extensionApi.runtime.sendMessage(message);
    }
  }

  // The request itself runs in the background script; src/background.js
  // explains why content scripts can't fetch the archive in Firefox.
  async function doFetch(path, params) {
    // Chrome keeps a tab's content scripts running after the extension is
    // updated or reloaded, but cuts them off from the new background.
    if (!extensionApi.runtime?.id) {
      throw new Error("the extension was updated, reload the page");
    }
    const reply = await sendToBackground({ type: "arctic-shift", path, params });
    if (!reply) throw new Error("no response from the extension background");
    if (reply.error) throw new Error(reply.error);
    return reply.data;
  }

  // Caches the promise rather than the settled value, so concurrent calls for
  // the same key share one request. Failed requests are evicted so errors
  // aren't cached.
  function call(path, params) {
    const key = cacheKey(path, params);
    const cached = cacheGet(key);
    if (cached) return cached;
    const promise = doFetch(path, params).catch((err) => {
      if (cache.get(key) === promise) cache.delete(key);
      throw err;
    });
    cachePut(key, promise);
    return promise;
  }

  async function searchPostsByAuthor(author, { limit = 100, before } = {}) {
    return call("/posts/search", { author, limit, sort: "desc", before });
  }

  async function searchCommentsByAuthor(author, { limit = 100, before } = {}) {
    return call("/comments/search", { author, limit, sort: "desc", before });
  }

  // Arctic Shift's /ids endpoints expect bare base-36 ids (no t1_/t3_ prefix).
  function bareIds(ids) {
    return ids
      .map((id) => String(id).replace(/^t[0-9]_/, ""))
      .filter(Boolean)
      .join(",");
  }

  async function getPostsByIds(ids, { fields } = {}) {
    const joined = bareIds(ids);
    if (!joined) return [];
    return call("/posts/ids", { ids: joined, fields });
  }

  async function getCommentsByIds(ids, { fields } = {}) {
    const joined = bareIds(ids);
    if (!joined) return [];
    return call("/comments/ids", { ids: joined, fields });
  }

  window.RU_ArcticShift = {
    searchPostsByAuthor,
    searchCommentsByAuthor,
    getPostsByIds,
    getCommentsByIds,
  };
})();
