"use strict";

(function () {
  const { el, formatDate, renderMarkdown, safeHref } = window.RU_Dom;
  const Arctic = window.RU_ArcticShift;

  const PANEL_ID = "ru-profile-panel";
  const POSTS_REGEX = /likes? to keep (?:their|her|his) posts? hidden/i;
  const COMMENTS_REGEX = /likes? to keep (?:their|her|his) comments? hidden/i;
  const WAIT_FOR_MESSAGE_MS = 10000;
  const STABILITY_MS = 350;
  // Coalesce observer-driven rescans so a burst of mutations during page
  // hydration triggers at most one full-document text walk per window, rather
  // than re-walking the whole DOM on every mutation batch.
  const SCAN_COALESCE_MS = 150;

  // Aborts the in-flight waitForHiddenMessage when a newer navigation supersedes
  // it, so stale observers don't keep walking the DOM in the background.
  let activeAbort = null;

  function parseProfileUsername() {
    const m = location.pathname.match(/^\/(?:user|u)\/([^\/?#]+)/i);
    return m ? m[1] : null;
  }

  function isReservedUser(name) {
    if (!name) return true;
    const lower = name.toLowerCase();
    return lower === "me" || lower === "[deleted]";
  }

  // Single text-node walk that matches both messages at once and stops as soon
  // as both are found, rather than traversing the document twice.
  function scanHiddenState() {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let postsEl = null;
    let commentsEl = null;
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const text = node.textContent;
      // Both messages contain the literal word "hidden"; this cheap substring
      // guard skips the two regex tests for the vast majority of text nodes.
      if (!text || !text.includes("hidden")) continue;
      if (!postsEl && POSTS_REGEX.test(text)) postsEl = node.parentElement;
      if (!commentsEl && COMMENTS_REGEX.test(text)) commentsEl = node.parentElement;
      if (postsEl && commentsEl) break;
    }
    return { postsEl, commentsEl };
  }

  function waitForHiddenMessage(signal) {
    return new Promise((resolve) => {
      let resolved = false;
      let stabilityTimer = null;
      let checkScheduled = null;
      let pendingState = null;

      const finalize = (state) => {
        if (resolved) return;
        resolved = true;
        clearTimeout(stabilityTimer);
        clearTimeout(checkScheduled);
        clearTimeout(timeoutTimer);
        observer.disconnect();
        if (signal) signal.removeEventListener("abort", onAbort);
        resolve(state);
      };

      const onAbort = () => finalize({ postsEl: null, commentsEl: null });

      const check = () => {
        if (resolved) return;
        const state = scanHiddenState();
        if (!state.postsEl && !state.commentsEl) return;

        // Only restart the stability timer when the candidate elements change,
        // so a settled message doesn't get reset by unrelated mutations.
        if (
          pendingState &&
          pendingState.postsEl === state.postsEl &&
          pendingState.commentsEl === state.commentsEl
        ) {
          return;
        }

        pendingState = state;
        clearTimeout(stabilityTimer);
        stabilityTimer = setTimeout(() => {
          if (resolved) return;
          const current = scanHiddenState();
          const postsStable = current.postsEl === pendingState.postsEl
            && (!current.postsEl || document.contains(current.postsEl));
          const commentsStable = current.commentsEl === pendingState.commentsEl
            && (!current.commentsEl || document.contains(current.commentsEl));
          if (postsStable && commentsStable) finalize(current);
        }, STABILITY_MS);
      };

      // The first mutation in a window schedules a single rescan; further
      // mutations fold into it instead of each kicking off a fresh walk.
      // setTimeout (not rAF) keeps this working in background tabs, where the
      // profile may be opened before the user switches to it.
      const scheduleCheck = () => {
        if (checkScheduled || resolved) return;
        checkScheduled = setTimeout(() => {
          checkScheduled = null;
          check();
        }, SCAN_COALESCE_MS);
      };

      const observer = new MutationObserver(scheduleCheck);

      if (signal) {
        if (signal.aborted) { resolve({ postsEl: null, commentsEl: null }); return; }
        signal.addEventListener("abort", onAbort);
      }

      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
      check();

      const timeoutTimer = setTimeout(() => finalize({ postsEl: null, commentsEl: null }), WAIT_FOR_MESSAGE_MS);
    });
  }

  // Climb from the message element through wrappers that exist solely for it,
  // stopping before an ancestor that holds other meaningful content — so the
  // panel lands right below the notice block, not below unrelated siblings.
  // (A fixed-depth climb breaks whenever Reddit changes its wrapper nesting.)
  function findInsertionAnchor(messageEl) {
    let node = messageEl;
    const msgLen = (messageEl.textContent || "").trim().length;
    for (let i = 0; i < 6; i++) {
      const parent = node.parentElement;
      if (!parent || parent === document.body || parent === document.documentElement) break;
      const tag = parent.tagName;
      if (tag === "MAIN" || tag === "ARTICLE" || tag === "SHREDDIT-APP") break;
      // The slack covers small decorations like the "Welcome!" heading; a
      // parent with substantially more text has real siblings — stop short.
      if ((parent.textContent || "").trim().length > msgLen + 120) break;
      node = parent;
    }
    return node;
  }

  function postLink(p) {
    if (!p) return "#";
    if (p.permalink) {
      const safe = safeHref(p.permalink);
      if (safe) return safe;
    }
    if (p.id) {
      return p.subreddit
        ? `https://www.reddit.com/r/${encodeURIComponent(p.subreddit)}/comments/${encodeURIComponent(p.id)}/`
        : `https://www.reddit.com/comments/${encodeURIComponent(p.id)}/`;
    }
    return "#";
  }

  function commentLink(c) {
    if (!c) return "#";
    if (c.permalink) {
      const safe = safeHref(c.permalink);
      if (safe) return safe;
    }
    const linkId = (c.link_id || "").replace(/^t3_/, "");
    if (linkId && c.id && c.subreddit) {
      return `https://www.reddit.com/r/${encodeURIComponent(c.subreddit)}/comments/${encodeURIComponent(linkId)}/_/${encodeURIComponent(c.id)}/`;
    }
    return "#";
  }

  function renderPostItem(p) {
    const subreddit = p.subreddit ? `r/${p.subreddit}` : "";
    const title = p.title || "(no title)";
    const meta = [subreddit, formatDate(p.created_utc), typeof p.score === "number" ? `${p.score} pts` : null].filter(Boolean).join(" · ");
    const permalink = postLink(p);
    const li = el(
      "li",
      { class: "ru-item" },
      el(
        "div",
        { class: "ru-item__head" },
        el("a", { class: "ru-item__title", href: permalink, target: "_blank", rel: "noopener noreferrer" }, title),
        el("span", { class: "ru-item__meta" }, meta)
      )
    );
    if (p.selftext) {
      const body = el("div", { class: "ru-item__body" });
      if (renderMarkdown(p.selftext, body)) li.append(body);
    }
    const extUrl = safeHref(p.url);
    if (extUrl && extUrl !== permalink) {
      li.append(el("a", { class: "ru-item__url", href: extUrl, target: "_blank", rel: "noopener noreferrer" }, extUrl));
    }
    return li;
  }

  function renderCommentItem(c) {
    const subreddit = c.subreddit ? `r/${c.subreddit}` : "";
    const meta = [subreddit, formatDate(c.created_utc), typeof c.score === "number" ? `${c.score} pts` : null].filter(Boolean).join(" · ");
    const li = el(
      "li",
      { class: "ru-item" },
      el(
        "div",
        { class: "ru-item__head" },
        el("a", { class: "ru-item__title ru-item__title--muted", href: commentLink(c), target: "_blank", rel: "noopener noreferrer" }, "Comment in " + (subreddit || "thread")),
        el("span", { class: "ru-item__meta" }, meta)
      )
    );
    if (c.body) {
      const body = el("div", { class: "ru-item__body" });
      if (renderMarkdown(c.body, body)) li.append(body);
    }
    return li;
  }

  function buildPanel(username, hasPosts, hasComments) {
    const sectionsLabel = [hasPosts ? "posts" : null, hasComments ? "comments" : null].filter(Boolean).join(" and ");
    const panel = el(
      "section",
      { id: PANEL_ID, class: "ru-panel", "data-username": username },
      el(
        "header",
        { class: "ru-panel__header" },
        el("span", { class: "ru-panel__badge" }, "Unhider"),
        el(
          "div",
          { class: "ru-panel__title-wrap" },
          el("h2", { class: "ru-panel__title" }, `Restoring hidden ${sectionsLabel} for u/${username}`)
        ),
        el(
          "button",
          {
            type: "button",
            class: "ru-panel__toggle",
            "aria-expanded": "true",
            onclick: (e) => {
              const expanded = e.currentTarget.getAttribute("aria-expanded") === "true";
              e.currentTarget.setAttribute("aria-expanded", expanded ? "false" : "true");
              panel.querySelector(".ru-panel__body").classList.toggle("ru-hidden", expanded);
              e.currentTarget.textContent = expanded ? "Show" : "Hide";
            },
          },
          "Hide"
        )
      ),
      el("div", { class: "ru-panel__body" })
    );
    return panel;
  }

  const PAGE_SIZE = 100;

  const SECTIONS = {
    posts: {
      noun: "posts",
      label: "Posts",
      fetchPage: (username, before) =>
        Arctic.searchPostsByAuthor(username, { limit: PAGE_SIZE, before }),
      renderItem: renderPostItem,
    },
    comments: {
      noun: "comments",
      label: "Comments",
      fetchPage: (username, before) =>
        Arctic.searchCommentsByAuthor(username, { limit: PAGE_SIZE, before }),
      renderItem: renderCommentItem,
    },
  };

  async function fillSection(slot, username, kind) {
    const { noun, label, fetchPage, renderItem } = SECTIONS[kind];
    slot.append(el("p", { class: "ru-slot--loading" }, `Loading ${noun} from archive…`));

    const seen = new Set();
    let total = 0;
    let oldestUtc = Infinity;

    const appendBatch = (list, items) => {
      let added = 0;
      for (const item of items) {
        if (item.id) {
          if (seen.has(item.id)) continue;
          seen.add(item.id);
        }
        if (typeof item.created_utc === "number" && item.created_utc < oldestUtc) {
          oldestUtc = item.created_utc;
        }
        list.append(renderItem(item));
        added++;
      }
      total += added;
      return added;
    };

    try {
      const first = await fetchPage(username, undefined);
      slot.replaceChildren();
      const heading = el("h3", { class: "ru-section-h" }, label);
      slot.append(heading);
      if (first.length === 0) {
        slot.append(el("p", { class: "ru-empty" }, `Archive has no ${noun} for this user.`));
        return;
      }
      const list = el("ul", { class: "ru-list" });
      slot.append(list);
      appendBatch(list, first);

      let hasMore = first.length >= PAGE_SIZE && oldestUtc !== Infinity;
      const updateHeading = () => {
        heading.textContent = `${label} (${total}${hasMore ? "+" : ""})`;
      };
      updateHeading();
      if (!hasMore) return;

      const moreBtn = el("button", { type: "button", class: "ru-load-more" }, `Load older ${noun}`);
      slot.append(moreBtn);
      moreBtn.addEventListener("click", async () => {
        slot.querySelectorAll(".ru-more-error").forEach((n) => n.remove());
        moreBtn.disabled = true;
        moreBtn.textContent = "Loading…";
        try {
          // before is exclusive; +1 re-includes items sharing the boundary
          // second, and the id set drops the repeats — nothing gets skipped.
          const batch = await fetchPage(username, Math.floor(oldestUtc) + 1);
          const added = appendBatch(list, batch);
          hasMore = batch.length >= PAGE_SIZE && added > 0;
          updateHeading();
          if (hasMore) {
            moreBtn.disabled = false;
            moreBtn.textContent = `Load older ${noun}`;
          } else {
            moreBtn.remove();
          }
        } catch (err) {
          moreBtn.disabled = false;
          moreBtn.textContent = `Load older ${noun}`;
          moreBtn.insertAdjacentElement(
            "beforebegin",
            el("p", { class: "ru-empty ru-empty--error ru-more-error" },
              `Couldn't load more: ` + (err.message || err))
          );
        }
      });
    } catch (err) {
      slot.replaceChildren();
      slot.append(el("h3", { class: "ru-section-h" }, label));
      slot.append(el("p", { class: "ru-empty ru-empty--error" }, `Couldn't load ${noun}: ` + (err.message || err)));
    }
  }

  async function insertPanel(username, postsEl, commentsEl) {
    const existing = document.getElementById(PANEL_ID);
    if (existing) return existing;

    const panel = buildPanel(username, !!postsEl, !!commentsEl);
    const body = panel.querySelector(".ru-panel__body");

    const postsSlot = postsEl ? el("div", { class: "ru-section" }) : null;
    const commentsSlot = commentsEl ? el("div", { class: "ru-section" }) : null;
    if (postsSlot) body.append(postsSlot);
    if (commentsSlot) body.append(commentsSlot);

    const anchorEl = postsEl || commentsEl;
    findInsertionAnchor(anchorEl).insertAdjacentElement("afterend", panel);

    await Promise.allSettled([
      postsSlot ? fillSection(postsSlot, username, "posts") : Promise.resolve(),
      commentsSlot ? fillSection(commentsSlot, username, "comments") : Promise.resolve(),
    ]);
    return panel;
  }

  // Resolves when the panel is no longer in the document (Reddit swapped out
  // the content region it was anchored in) or the run is superseded. Each
  // mutation batch costs one isConnected check — no tree walk.
  function waitForPanelRemoval(panel, signal) {
    return new Promise((resolve) => {
      if (signal.aborted || !panel.isConnected) {
        resolve();
        return;
      }
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        observer.disconnect();
        signal.removeEventListener("abort", finish);
        resolve();
      };
      const observer = new MutationObserver(() => {
        if (!panel.isConnected) finish();
      });
      observer.observe(document.body, { childList: true, subtree: true });
      signal.addEventListener("abort", finish);
    });
  }

  // When the user switches profile tabs, Reddit swaps the content in
  // asynchronously — a scan can match the outgoing tab's notice, anchoring the
  // panel to a node the pending swap then destroys. Capped so a pathological
  // page that keeps churning the DOM can't make us refetch from the archive
  // forever.
  const MAX_PANEL_INSERTS = 5;

  async function run() {
    // Supersede any wait still running from a previous navigation.
    if (activeAbort) activeAbort.abort();
    activeAbort = null;

    const username = parseProfileUsername();
    document.getElementById(PANEL_ID)?.remove();
    if (!username || isReservedUser(username)) return;

    // old.reddit.com (or www served in legacy mode) has no "keeps their posts
    // hidden" notice — a hidden profile just renders the empty-listing marker.
    // The page is server-rendered and static, so one synchronous pass is enough.
    const oldRedditMarker = document.getElementById("noresults");
    if (oldRedditMarker) {
      await insertPanel(username, oldRedditMarker, oldRedditMarker);
      return;
    }

    const ac = new AbortController();
    activeAbort = ac;
    const { signal } = ac;
    const startPath = location.pathname;

    // Reconcile until the DOM settles: find the notice, insert the panel, and
    // if a late content swap sweeps the panel away while we're still on the
    // same path, scan again and re-anchor it in the new content.
    for (let attempt = 0; attempt < MAX_PANEL_INSERTS; attempt++) {
      const { postsEl, commentsEl } = await waitForHiddenMessage(signal);
      if (signal.aborted || location.pathname !== startPath) return;
      if (!postsEl && !commentsEl) return;

      const panel = await insertPanel(username, postsEl, commentsEl);
      if (panel) await waitForPanelRemoval(panel, signal);
      if (signal.aborted || location.pathname !== startPath) return;
    }
  }

  window.RU_Profile = { run };
})();
