"use strict";

(function () {
  const { el, formatDate, renderMarkdown, safeHref } = window.RU_Dom;
  const Arctic = window.RU_ArcticShift;

  const PANEL_ID = "ru-profile-panel";
  const POSTS_REGEX = /likes? to keep (?:their|her|his) posts? hidden/i;
  const COMMENTS_REGEX = /likes? to keep (?:their|her|his) comments? hidden/i;
  const WAIT_FOR_MESSAGE_MS = 10000;
  const STABILITY_MS = 350;

  function parseProfileUsername() {
    const m = location.pathname.match(/^\/(?:user|u)\/([^\/?#]+)/i);
    return m ? m[1] : null;
  }

  function isReservedUser(name) {
    if (!name) return true;
    const lower = name.toLowerCase();
    return lower === "me" || lower === "[deleted]";
  }

  function findMessageElement(regex) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        return regex.test(node.textContent || "")
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT;
      },
    });
    const node = walker.nextNode();
    return node ? node.parentElement : null;
  }

  function scanHiddenState() {
    const postsEl = findMessageElement(POSTS_REGEX);
    const commentsEl = findMessageElement(COMMENTS_REGEX);
    return { postsEl, commentsEl };
  }

  function waitForHiddenMessage() {
    return new Promise((resolve) => {
      let resolved = false;
      let stabilityTimer = null;
      let pendingState = null;

      const finalize = (state) => {
        if (resolved) return;
        resolved = true;
        clearTimeout(stabilityTimer);
        clearTimeout(timeoutTimer);
        observer.disconnect();
        resolve(state);
      };

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

      const observer = new MutationObserver(check);
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
      check();

      const timeoutTimer = setTimeout(() => finalize({ postsEl: null, commentsEl: null }), WAIT_FOR_MESSAGE_MS);
    });
  }

  function findInsertionAnchor(messageEl) {
    let node = messageEl;
    for (let i = 0; i < 4 && node.parentElement; i++) {
      node = node.parentElement;
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
    const li = el(
      "li",
      { class: "ru-item" },
      el(
        "div",
        { class: "ru-item__head" },
        el("a", { class: "ru-item__title", href: postLink(p), target: "_blank", rel: "noopener noreferrer" }, title),
        el("span", { class: "ru-item__meta" }, meta)
      )
    );
    if (p.selftext) {
      const body = el("div", { class: "ru-item__body" });
      if (renderMarkdown(p.selftext, body)) li.append(body);
    }
    const extUrl = safeHref(p.url);
    if (extUrl && extUrl !== postLink(p)) {
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

  async function fillPostsSection(slot, username) {
    slot.append(el("p", { class: "ru-slot--loading" }, "Loading posts from archive…"));
    try {
      const posts = await Arctic.searchPostsByAuthor(username, { limit: 100 });
      slot.innerHTML = "";
      slot.append(
        el("h3", { class: "ru-section-h" }, `Posts (${posts.length === 100 ? "100+" : posts.length})`)
      );
      if (posts.length === 0) {
        slot.append(el("p", { class: "ru-empty" }, "Archive has no posts for this user."));
        return;
      }
      const list = el("ul", { class: "ru-list" });
      for (const p of posts) list.append(renderPostItem(p));
      slot.append(list);
    } catch (err) {
      slot.innerHTML = "";
      slot.append(el("h3", { class: "ru-section-h" }, "Posts"));
      slot.append(el("p", { class: "ru-empty ru-empty--error" }, "Couldn't load posts: " + (err.message || err)));
    }
  }

  async function fillCommentsSection(slot, username) {
    slot.append(el("p", { class: "ru-slot--loading" }, "Loading comments from archive…"));
    try {
      const comments = await Arctic.searchCommentsByAuthor(username, { limit: 100 });
      slot.innerHTML = "";
      slot.append(
        el("h3", { class: "ru-section-h" }, `Comments (${comments.length === 100 ? "100+" : comments.length})`)
      );
      if (comments.length === 0) {
        slot.append(el("p", { class: "ru-empty" }, "Archive has no comments for this user."));
        return;
      }
      const list = el("ul", { class: "ru-list" });
      for (const c of comments) list.append(renderCommentItem(c));
      slot.append(list);
    } catch (err) {
      slot.innerHTML = "";
      slot.append(el("h3", { class: "ru-section-h" }, "Comments"));
      slot.append(el("p", { class: "ru-empty ru-empty--error" }, "Couldn't load comments: " + (err.message || err)));
    }
  }

  async function run() {
    const username = parseProfileUsername();
    document.getElementById(PANEL_ID)?.remove();
    if (!username || isReservedUser(username)) return;

    const startPath = location.pathname;
    const { postsEl, commentsEl } = await waitForHiddenMessage();
    if (location.pathname !== startPath) return;
    if (!postsEl && !commentsEl) return;

    if (document.getElementById(PANEL_ID)) return;

    const panel = buildPanel(username, !!postsEl, !!commentsEl);
    const body = panel.querySelector(".ru-panel__body");

    const postsSlot = postsEl ? el("div", { class: "ru-section" }) : null;
    const commentsSlot = commentsEl ? el("div", { class: "ru-section" }) : null;
    if (postsSlot) body.append(postsSlot);
    if (commentsSlot) body.append(commentsSlot);

    const anchorEl = postsEl || commentsEl;
    findInsertionAnchor(anchorEl).insertAdjacentElement("afterend", panel);

    await Promise.allSettled([
      postsSlot ? fillPostsSection(postsSlot, username) : Promise.resolve(),
      commentsSlot ? fillCommentsSection(commentsSlot, username) : Promise.resolve(),
    ]);
  }

  window.RU_Profile = { run };
})();
