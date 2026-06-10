"use strict";

(function () {
  const RUN_DEBOUNCE_MS = 300;
  let pending = null;
  // null forces the initial dispatch; afterwards dispatch only fires when the
  // href actually changed, so navigate events for canceled or cross-document
  // navigations don't tear down and rebuild the panel for nothing.
  let lastDispatchedHref = null;

  function isProfileRoute() {
    return /^\/(?:user|u)\/[^\/]+/i.test(location.pathname);
  }

  function dispatch() {
    if (location.href === lastDispatchedHref) return;
    lastDispatchedHref = location.href;
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
    if (location.href !== lastDispatchedHref) scheduleDispatch();
  }

  // Content scripts run in an isolated world with their own History wrapper,
  // so patching history.pushState here never sees the page's own calls —
  // Reddit's SPA router is invisible to a History patch from this side. The
  // Navigation API (Chrome 102+) does fire in the isolated world for every
  // navigation, but with two traps: destination.sameDocument is false for link
  // clicks the page's router intercept()s into a soft navigation (exactly how
  // Reddit switches profile tabs), and the URL hasn't committed yet when the
  // event fires. So don't filter on the event at all — schedule, and let the
  // debounced dispatch compare hrefs once the navigation has settled.
  window.addEventListener("popstate", notifyLocationChange);
  if (window.navigation && typeof window.navigation.addEventListener === "function") {
    window.navigation.addEventListener("navigate", () => scheduleDispatch());
  } else {
    // No Navigation API (e.g. Firefox): fall back to a visibility-gated poll.
    setInterval(() => {
      if (!document.hidden) notifyLocationChange();
    }, 500);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) notifyLocationChange();
    });
  }

  scheduleDispatch();
})();
