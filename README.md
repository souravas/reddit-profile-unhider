# Reddit Profile Unhider

Chrome extension that automatically reveals a Reddit user's posts and comments when they've hidden them on their profile.

When you visit a user page and Reddit shows:

> u/&lt;name&gt; likes to keep their posts hidden, but check out their stats to learn more about them.

…this extension detects that message, pulls the user's archived posts/comments from [Arctic Shift](https://arctic-shift.photon-reddit.com/), and renders them in a panel right below the message. No button click — it happens automatically.

## Install

Install from the Chrome Web Store: [Reddit Profile Unhider](https://chromewebstore.google.com/detail/reddit-profile-unhider/apcnakinkkhopllilmienljcgmaaigld)

Then visit any user profile that's marked as hidden — e.g., `https://www.reddit.com/user/<name>/`

## How it works

A single content script runs on `www.reddit.com` and `sh.reddit.com`:

1. [src/main.js](src/main.js) detects user-profile URLs and re-runs on SPA navigation (by patching `history.pushState`/`replaceState`)
2. [src/profile.js](src/profile.js) watches the DOM for the "likes to keep their posts/comments hidden" message via `MutationObserver`
3. When detected, it calls Arctic Shift's `/api/posts/search?author=<name>` and `/api/comments/search?author=<name>` ([src/arctic-shift.js](src/arctic-shift.js))
4. Results are rendered in a `.ru-panel` styled by [src/styles.css](src/styles.css)

Only what's hidden is fetched. If only comments are hidden, only comments are loaded. If both are hidden, both are loaded.

## Permissions

- Content script runs on `www.reddit.com` and `sh.reddit.com` (via the manifest's `content_scripts.matches` — no broader page access).
- One host permission: `https://arctic-shift.photon-reddit.com/*`, used to fetch archived posts/comments. Without it, MV3 blocks the cross-origin request.

No `tabs`, `storage`, `cookies`, or other Chrome APIs are requested.

## Limitations

- **Archive coverage**: Content deleted within minutes of being posted may not be in Arctic Shift.
- **Cap**: 100 posts + 100 comments per profile (Arctic Shift's per-query maximum). For very prolific users, only the most recent are shown.
- **New Reddit only** (`www.reddit.com`, `sh.reddit.com`).

## Files

```
manifest.json           MV3 manifest
src/arctic-shift.js     Arctic Shift API client
src/dom.js              DOM helpers
src/profile.js          Hidden-profile detection + render
src/main.js             SPA navigation router
src/styles.css          Panel styles
src/popup.html          Toolbar popup (lookup-by-username shortcut)
src/popup.js
icons/                  Toolbar icons
```
