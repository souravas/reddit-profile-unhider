"use strict";

(function () {
  const DATE_FMT = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  function formatDate(epochSeconds) {
    if (!epochSeconds) return "";
    return DATE_FMT.format(new Date(epochSeconds * 1000));
  }

  function safeHref(href) {
    if (!href) return null;
    try {
      const u = new URL(href, "https://www.reddit.com/");
      return u.protocol === "http:" || u.protocol === "https:" ? u.href : null;
    } catch {
      return null;
    }
  }

  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === false || v == null) continue;
      if (k === "class") node.className = v;
      else if (k.startsWith("on") && typeof v === "function") {
        node.addEventListener(k.slice(2).toLowerCase(), v);
      } else {
        node.setAttribute(k, v === true ? "" : v);
      }
    }
    for (const child of children.flat()) {
      if (child == null || child === false) continue;
      node.append(child.nodeType ? child : document.createTextNode(child));
    }
    return node;
  }

  // Allowlist inline markdown rendered via DOM APIs only — no innerHTML, no HTML parsing.
  const INLINE_RE = /(`[^`\n]+`)|(\*\*[^*\n]+\*\*)|(__[^_\n]+__)|(\*[^*\n]+\*)|(_[^_\n]+_)|(\[([^\]\n]+)\]\((https?:\/\/[^)\s]+|\/[^)\s]+)\))|(https?:\/\/[^\s<>"')\]]+)/g;

  function makeLink(href, text) {
    const safe = safeHref(href);
    if (!safe) return null;
    const a = document.createElement("a");
    a.href = safe;
    a.textContent = text;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }

  function appendTextWithBreaks(container, text) {
    const parts = text.split("\n");
    for (let i = 0; i < parts.length; i++) {
      if (i > 0) container.append(document.createElement("br"));
      if (parts[i]) container.append(document.createTextNode(parts[i]));
    }
  }

  function renderInline(text, container) {
    let last = 0;
    for (const m of text.matchAll(INLINE_RE)) {
      if (m.index > last) appendTextWithBreaks(container, text.slice(last, m.index));
      if (m[1]) {
        const code = document.createElement("code");
        code.textContent = m[1].slice(1, -1);
        container.append(code);
      } else if (m[2] || m[3]) {
        const s = document.createElement("strong");
        s.textContent = (m[2] || m[3]).slice(2, -2);
        container.append(s);
      } else if (m[4] || m[5]) {
        const e = document.createElement("em");
        e.textContent = (m[4] || m[5]).slice(1, -1);
        container.append(e);
      } else if (m[6]) {
        const link = makeLink(m[8], m[7]);
        if (link) container.append(link);
        else appendTextWithBreaks(container, m[6]);
      } else if (m[9]) {
        const link = makeLink(m[9], m[9]);
        if (link) container.append(link);
        else appendTextWithBreaks(container, m[9]);
      }
      last = m.index + m[0].length;
    }
    if (last < text.length) appendTextWithBreaks(container, text.slice(last));
  }

  // Archive text is untrusted; cap blockquote nesting so pathological input
  // (thousands of stacked ">" levels) can't recurse until the stack blows.
  const MAX_QUOTE_DEPTH = 10;

  function renderMarkdown(md, container, depth = 0) {
    if (!md) return false;
    const lines = String(md).replace(/\r\n/g, "\n").split("\n");
    let i = 0;
    let rendered = false;
    while (i < lines.length) {
      const line = lines[i];
      if (!line.trim()) { i++; continue; }

      if (/^```/.test(line)) {
        const start = i + 1;
        let end = start;
        while (end < lines.length && !/^```/.test(lines[end])) end++;
        const pre = document.createElement("pre");
        const code = document.createElement("code");
        code.textContent = lines.slice(start, end).join("\n");
        pre.append(code);
        container.append(pre);
        rendered = true;
        i = end + 1;
        continue;
      }

      if (/^>\s?/.test(line)) {
        const buf = [];
        while (i < lines.length && /^>\s?/.test(lines[i])) {
          buf.push(lines[i].replace(/^>\s?/, ""));
          i++;
        }
        const bq = document.createElement("blockquote");
        if (depth < MAX_QUOTE_DEPTH) {
          renderMarkdown(buf.join("\n"), bq, depth + 1);
        } else {
          renderInline(buf.join("\n"), bq);
        }
        container.append(bq);
        rendered = true;
        continue;
      }

      if (/^[-*+]\s+/.test(line)) {
        const ul = document.createElement("ul");
        while (i < lines.length && /^[-*+]\s+/.test(lines[i])) {
          const li = document.createElement("li");
          renderInline(lines[i].replace(/^[-*+]\s+/, ""), li);
          ul.append(li);
          i++;
        }
        container.append(ul);
        rendered = true;
        continue;
      }

      if (/^\d+\.\s+/.test(line)) {
        const ol = document.createElement("ol");
        while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
          const li = document.createElement("li");
          renderInline(lines[i].replace(/^\d+\.\s+/, ""), li);
          ol.append(li);
          i++;
        }
        container.append(ol);
        rendered = true;
        continue;
      }

      const para = [];
      while (
        i < lines.length &&
        lines[i].trim() &&
        !/^(?:```|>|[-*+]\s+|\d+\.\s+)/.test(lines[i])
      ) {
        para.push(lines[i]);
        i++;
      }
      const p = document.createElement("p");
      renderInline(para.join("\n"), p);
      container.append(p);
      rendered = true;
    }
    return rendered;
  }

  window.RU_Dom = { formatDate, el, safeHref, renderMarkdown };
})();
