"use strict";

(function () {
  const API_BASE = "https://arctic-shift.photon-reddit.com/api";
  const REQUEST_TIMEOUT_MS = 20000;
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

  async function timedFetch(url, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      clearTimeout(timer);
    }
  }

  async function call(path, params) {
    const key = cacheKey(path, params);
    const cached = cacheGet(key);
    if (cached) return cached;
    const url = new URL(`${API_BASE}${path}`);
    for (const [k, v] of Object.entries(params)) {
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
    const data = json && Array.isArray(json.data) ? json.data : [];
    cachePut(key, data);
    return data;
  }

  async function searchPostsByAuthor(author, { limit = 100 } = {}) {
    return call("/posts/search", { author, limit, sort: "desc" });
  }

  async function searchCommentsByAuthor(author, { limit = 100 } = {}) {
    return call("/comments/search", { author, limit, sort: "desc" });
  }

  window.RU_ArcticShift = { searchPostsByAuthor, searchCommentsByAuthor };
})();
