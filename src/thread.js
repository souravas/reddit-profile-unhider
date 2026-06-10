"use strict";

(function () {
  const { el, formatDate, renderMarkdown, safeHref } = window.RU_Dom;
  const Arctic = window.RU_ArcticShift;

  const SCAN_DEBOUNCE_MS = 250;

  // Body text shown in place of removed/deleted content. Anchored to the start so
  // a normal comment merely mentioning "[removed]" mid-sentence isn't matched.
  const REMOVED_RE = /^\s*(\[removed\]|\[deleted\]|Comment removed by moderator|Comment deleted by user|Comment removed|Comment deleted|Removed by Reddit|Sorry, this post was removed)/i;
  const BLANK_RE = /^\s*(\[removed\]|\[deleted\])\s*$/i;

  let activeObserver = null;
  let scanScheduled = null;

  function isThreadPath() {
    return /^\/(?:r\/[^/]+\/)?comments\/[a-z0-9]+/i.test(location.pathname);
  }

  // A comment's own body, excluding bodies of nested child comments.
  function ownBody(comment) {
    const candidates = comment.querySelectorAll(".md");
    for (const md of candidates) {
      if (md.closest("shreddit-comment") === comment) return md;
    }
    return null;
  }

  function metaLine(author, createdUtc) {
    const parts = [
      author ? `u/${author}` : null,
      formatDate(createdUtc),
      "restored from archive",
    ].filter(Boolean);
    return el("div", { class: "ru-restored__meta" }, parts.join(" · "));
  }

  function bodyBlock(text) {
    const div = el("div", { class: "ru-restored__body" });
    if (!renderMarkdown(text, div)) div.textContent = text;
    return div;
  }

  function emptyBlock(message) {
    const block = el("div", { class: "ru-restored ru-restored--empty" });
    block.append(el("div", { class: "ru-restored__note" }, message));
    return block;
  }

  async function buildCommentBlock(id) {
    const data = await Arctic.getCommentsByIds([id], {
      fields: "id,author,body,created_utc",
    });
    const c = data && data[0];
    if (!c) return emptyBlock("Not in the archive.");
    const author = c.author && c.author !== "[deleted]" ? c.author : null;
    const block = el("div", { class: "ru-restored" }, metaLine(author, c.created_utc));
    if (!c.body || BLANK_RE.test(c.body)) {
      block.append(el("div", { class: "ru-restored__note" }, "Archive copy is also blank (saved after removal)."));
    } else {
      block.append(bodyBlock(c.body));
    }
    return block;
  }

  async function buildPostBlock(id) {
    const data = await Arctic.getPostsByIds([id], {
      fields: "id,author,title,selftext,url,created_utc",
    });
    const p = data && data[0];
    if (!p) return emptyBlock("Not in the archive.");
    const author = p.author && p.author !== "[deleted]" ? p.author : null;
    const block = el("div", { class: "ru-restored" }, metaLine(author, p.created_utc));
    if (p.selftext && !BLANK_RE.test(p.selftext)) {
      block.append(bodyBlock(p.selftext));
    } else {
      // Link posts have no selftext; surface the original external URL instead.
      const link = safeHref(p.url);
      if (link && !/^https?:\/\/(?:www\.|sh\.|old\.)?reddit\.com\//i.test(link)) {
        block.append(el("a", { class: "ru-restored__url", href: link, target: "_blank", rel: "noopener noreferrer" }, link));
      } else {
        block.append(el("div", { class: "ru-restored__note" }, "Archive copy is also blank (saved after removal)."));
      }
    }
    return block;
  }

  async function reveal(wrap, btn, kind, id) {
    // Drop any restored/error block left by a prior attempt before retrying.
    wrap.querySelectorAll(".ru-restored").forEach((n) => n.remove());
    btn.disabled = true;
    btn.textContent = "Restoring…";
    try {
      const block = kind === "post" ? await buildPostBlock(id) : await buildCommentBlock(id);
      btn.remove();
      wrap.append(block);
    } catch (err) {
      btn.disabled = false;
      btn.textContent = "Reveal archived";
      wrap.append(
        el("div", { class: "ru-restored ru-restored--error" },
          el("div", { class: "ru-restored__note" }, "Couldn't load from archive: " + (err && err.message ? err.message : String(err))))
      );
    }
  }

  function injectReveal(anchorEl, kind, id) {
    const wrap = el("div", { class: "ru-restore-wrap" });
    const btn = el(
      "button",
      { type: "button", class: "ru-reveal", onclick: () => reveal(wrap, btn, kind, id) },
      "Reveal archived"
    );
    wrap.append(btn);
    anchorEl.insertAdjacentElement("afterend", wrap);
  }

  function scanPost() {
    const post = document.querySelector("shreddit-post:not([data-ru-reveal])");
    if (!post || !post.id) return;
    const body =
      document.getElementById(`${post.id}-post-rtjson-content`) ||
      post.querySelector('[slot="text-body"] .md');
    if (!body || !REMOVED_RE.test(body.textContent.trim())) return;
    post.setAttribute("data-ru-reveal", "1");
    injectReveal(body, "post", post.id);
  }

  function scanComment(comment) {
    const body = ownBody(comment);
    if (!body) return; // not hydrated yet; a later scan will catch it
    const author = comment.getAttribute("author");
    const removed = author === "[deleted]" || REMOVED_RE.test(body.textContent.trim());
    if (!removed) return;
    const thingid = comment.getAttribute("thingid");
    if (!thingid) return;
    comment.setAttribute("data-ru-reveal", "1");
    injectReveal(body, "comment", thingid);
  }

  // ---- old.reddit.com (and www.reddit.com served in legacy mode) ----

  // A comment's own body, excluding bodies of nested child comments (which
  // live under a sibling .child container, after the .entry).
  function oldOwnBody(thing) {
    const entry = thing.querySelector(":scope > .entry");
    return entry ? entry.querySelector(".usertext-body .md") : null;
  }

  function scanOldPost() {
    const post = document.querySelector("#siteTable .thing.link:not([data-ru-reveal])");
    if (!post) return;
    const body = post.querySelector(".entry .usertext-body .md");
    if (!body || !REMOVED_RE.test(body.textContent.trim())) return;
    const id = (post.getAttribute("data-fullname") || "").replace(/^t3_/, "");
    if (!id) return;
    post.setAttribute("data-ru-reveal", "1");
    injectReveal(body, "post", id);
  }

  function scanOldComments() {
    for (const thing of document.querySelectorAll(".commentarea .thing.comment:not([data-ru-reveal])")) {
      const body = oldOwnBody(thing);
      if (!body) continue;
      const removed = thing.classList.contains("deleted") || REMOVED_RE.test(body.textContent.trim());
      if (!removed) continue;
      const id = (thing.getAttribute("data-fullname") || "").replace(/^t1_/, "");
      if (!id) continue;
      thing.setAttribute("data-ru-reveal", "1");
      injectReveal(body, "comment", id);
    }
  }

  function scanRemoved() {
    if (!isThreadPath()) {
      teardown();
      return;
    }
    // Both DOM dialects are scanned; on each page only one set of selectors
    // matches, so the other is a no-op.
    scanPost();
    for (const comment of document.querySelectorAll("shreddit-comment:not([data-ru-reveal])")) {
      scanComment(comment);
    }
    scanOldPost();
    scanOldComments();
  }

  function scheduleScan() {
    if (scanScheduled) return;
    scanScheduled = setTimeout(() => {
      scanScheduled = null;
      scanRemoved();
    }, SCAN_DEBOUNCE_MS);
  }

  function teardown() {
    if (activeObserver) {
      activeObserver.disconnect();
      activeObserver = null;
    }
    if (scanScheduled) {
      clearTimeout(scanScheduled);
      scanScheduled = null;
    }
  }

  // Called on every navigation. Tears down a previous thread's observer first, so
  // leaving a thread (to a profile, feed, etc.) stops the scan and doesn't leak.
  function run() {
    teardown();
    if (!isThreadPath()) return;
    scanRemoved();
    activeObserver = new MutationObserver(scheduleScan);
    activeObserver.observe(document.body, { childList: true, subtree: true });
  }

  window.RU_Thread = { run };
})();
