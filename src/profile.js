"use strict";

(function () {
  const { el, escapeHTML, formatDate, safeHtmlFromArchive } = window.RU_Dom;
  const Arctic = window.RU_ArcticShift;

  const PANEL_ID = "ru-profile-panel";
  const POSTS_REGEX = /likes? to keep (?:their|her|his) posts? hidden/i;
  const COMMENTS_REGEX = /likes? to keep (?:their|her|his) comments? hidden/i;
  const WAIT_FOR_MESSAGE_MS = 10000;

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
      const initial = scanHiddenState();
      if (initial.postsEl || initial.commentsEl) return resolve(initial);

      let resolved = false;
      const observer = new MutationObserver(() => {
        const state = scanHiddenState();
        if (state.postsEl || state.commentsEl) {
          if (resolved) return;
          resolved = true;
          observer.disconnect();
          resolve(state);
        }
      });
      observer.observe(document.body, { childList: true, subtree: true, characterData: true });
      setTimeout(() => {
        if (resolved) return;
        resolved = true;
        observer.disconnect();
        resolve(scanHiddenState());
      }, WAIT_FOR_MESSAGE_MS);
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
    if (p.permalink) return new URL(p.permalink, "https://www.reddit.com/").href;
    if (p.id) {
      return p.subreddit
        ? `https://www.reddit.com/r/${p.subreddit}/comments/${p.id}/`
        : `https://www.reddit.com/comments/${p.id}/`;
    }
    return "#";
  }

  function commentLink(c) {
    if (!c) return "#";
    if (c.permalink) return new URL(c.permalink, "https://www.reddit.com/").href;
    const linkId = (c.link_id || "").replace(/^t3_/, "");
    if (linkId && c.id && c.subreddit) {
      return `https://www.reddit.com/r/${c.subreddit}/comments/${linkId}/_/${c.id}/`;
    }
    return "#";
  }

  function renderPostItem(p) {
    const subreddit = p.subreddit ? `r/${p.subreddit}` : "";
    const title = p.title || "(no title)";
    const bodyHtml = safeHtmlFromArchive(p.selftext_html) || (p.selftext ? `<p>${escapeHTML(p.selftext)}</p>` : "");
    const meta = [subreddit, formatDate(p.created_utc), typeof p.score === "number" ? `${p.score} pts` : null].filter(Boolean).join(" · ");
    return el(
      "li",
      { class: "ru-item" },
      el(
        "div",
        { class: "ru-item__head" },
        el("a", { class: "ru-item__title", href: postLink(p), target: "_blank", rel: "noopener" }, title),
        el("span", { class: "ru-item__meta" }, meta)
      ),
      bodyHtml ? el("div", { class: "ru-item__body", html: bodyHtml }) : null,
      p.url && p.url !== postLink(p) ? el("a", { class: "ru-item__url", href: p.url, target: "_blank", rel: "noopener" }, p.url) : null
    );
  }

  function renderCommentItem(c) {
    const subreddit = c.subreddit ? `r/${c.subreddit}` : "";
    const bodyHtml = safeHtmlFromArchive(c.body_html) || (c.body ? `<p>${escapeHTML(c.body)}</p>` : "");
    const meta = [subreddit, formatDate(c.created_utc), typeof c.score === "number" ? `${c.score} pts` : null].filter(Boolean).join(" · ");
    return el(
      "li",
      { class: "ru-item" },
      el(
        "div",
        { class: "ru-item__head" },
        el("a", { class: "ru-item__title ru-item__title--muted", href: commentLink(c), target: "_blank", rel: "noopener" }, "Comment in " + (subreddit || "thread")),
        el("span", { class: "ru-item__meta" }, meta)
      ),
      bodyHtml ? el("div", { class: "ru-item__body", html: bodyHtml }) : null
    );
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
          el("h2", { class: "ru-panel__title" }, `Restoring hidden ${sectionsLabel} for u/${username}`),
          el("p", { class: "ru-panel__sub" }, "Pulled from the Arctic Shift archive.")
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

    const { postsEl, commentsEl } = await waitForHiddenMessage();
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
