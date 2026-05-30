"use strict";

(function () {
  const RUN_DEBOUNCE_MS = 300;
  let pending = null;
  let lastHref = location.href;

  function isProfileRoute() {
    return /^\/(?:user|u)\/[^\/]+/i.test(location.pathname);
  }

  function dispatch() {
    lastHref = location.href;
    document.getElementById("ru-profile-panel")?.remove();
    if (isProfileRoute()) {
      window.RU_Profile.run().catch((err) => console.warn("[unhider] profile run failed", err));
    }
    // Self-gates on thread routes and tears down its observer when leaving one,
    // so it's safe (and necessary, for cleanup) to call on every navigation.
    try {
      window.RU_Thread.run();
    } catch (err) {
      console.warn("[unhider] thread run failed", err);
    }
  }

  function scheduleDispatch() {
    if (pending) clearTimeout(pending);
    pending = setTimeout(() => {
      pending = null;
      dispatch();
    }, RUN_DEBOUNCE_MS);
  }

  function notifyLocationChange() {
    if (location.href === lastHref) return;
    lastHref = location.href;
    scheduleDispatch();
  }

  // Primary signal across all engines: Reddit's SPA router navigates via the
  // History API, and popstate covers back/forward.
  for (const method of ["pushState", "replaceState"]) {
    const original = history[method];
    history[method] = function () {
      const result = original.apply(this, arguments);
      notifyLocationChange();
      return result;
    };
  }
  window.addEventListener("popstate", notifyLocationChange);

  // The Navigation API (Chrome 102+) emits a single "navigate" event for every
  // same-document navigation, including ones that bypass the History API. Where
  // it exists it fully covers the gap the poll below was guarding, so we listen
  // to it instead of polling. The event fires before the URL commits, so defer
  // the href check to the debounced dispatch. Fall back to a visibility-gated
  // poll only on engines without the Navigation API.
  if (window.navigation && typeof window.navigation.addEventListener === "function") {
    window.navigation.addEventListener("navigate", (e) => {
      if (e.destination && e.destination.sameDocument) scheduleDispatch();
    });
  } else {
    setInterval(() => {
      if (!document.hidden) notifyLocationChange();
    }, 500);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) notifyLocationChange();
    });
  }

  scheduleDispatch();
})();
