"use strict";

document.getElementById("lookup").addEventListener("submit", (e) => {
  e.preventDefault();
  const raw = document.getElementById("username").value.trim().replace(/^\/?u\//i, "").replace(/^@/, "");
  if (!raw) return;
  const url = `https://www.reddit.com/user/${encodeURIComponent(raw)}/`;
  chrome.tabs.create({ url });
});
