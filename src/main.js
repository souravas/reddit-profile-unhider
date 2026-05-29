"use strict";

(function () {
  const RUN_DEBOUNCE_MS = 300;
  let pending = null;

  function isProfileRoute() {
    return /^\/(?:user|u)\/[^\/]+/i.test(location.pathname);
  }

  function dispatch() {
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

  let lastHref = location.href;

  function notifyLocationChange() {
    lastHref = location.href;
    window.dispatchEvent(new Event("ru:locationchange"));
  }

  for (const method of ["pushState", "replaceState"]) {
    const original = history[method];
    history[method] = function () {
      const result = original.apply(this, arguments);
      notifyLocationChange();
      return result;
    };
  }
  window.addEventListener("popstate", notifyLocationChange);
  window.addEventListener("ru:locationchange", scheduleDispatch);

  // Fallback poll for navigations that bypass pushState/popstate (e.g. the
  // Navigation API or framework-internal routing). Routed through
  // notifyLocationChange so a primary signal doesn't fire a second time here.
  setInterval(() => {
    if (location.href !== lastHref) notifyLocationChange();
  }, 500);

  scheduleDispatch();
})();
