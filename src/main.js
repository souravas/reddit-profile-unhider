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
  }

  function scheduleDispatch() {
    if (pending) clearTimeout(pending);
    pending = setTimeout(() => {
      pending = null;
      dispatch();
    }, RUN_DEBOUNCE_MS);
  }

  for (const method of ["pushState", "replaceState"]) {
    const original = history[method];
    history[method] = function () {
      const result = original.apply(this, arguments);
      window.dispatchEvent(new Event("ru:locationchange"));
      return result;
    };
  }
  window.addEventListener("popstate", () => window.dispatchEvent(new Event("ru:locationchange")));
  window.addEventListener("ru:locationchange", scheduleDispatch);

  scheduleDispatch();
})();
