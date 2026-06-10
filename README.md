# Reddit Profile Unhider

Chrome extension that automatically reveals a Reddit user's posts and comments when they've hidden them on their profile.

When you visit a user page and Reddit shows:

> u/&lt;name&gt; likes to keep their posts hidden, but check out their stats to learn more about them.

…this extension detects that message, pulls the user's archived posts/comments from [Arctic Shift](https://arctic-shift.photon-reddit.com/), and renders them in a panel right below the message. No button click — it happens automatically.

## Install

Install from the Chrome Web Store: [Reddit Profile Unhider](https://chromewebstore.google.com/detail/reddit-profile-unhider/apcnakinkkhopllilmienljcgmaaigld)

Then visit any user profile that's marked as hidden — e.g., `https://www.reddit.com/user/<name>/`

## How it works

A single content script runs on `www.reddit.com`, `sh.reddit.com`, and `old.reddit.com`:

1. [src/main.js](src/main.js) detects user-profile URLs and re-runs on SPA navigation (the Navigation API where available, with a poll fallback elsewhere)
2. [src/profile.js](src/profile.js) watches the DOM for the "likes to keep their posts/comments hidden" message via `MutationObserver`. On old Reddit (which has no such notice), an empty profile listing triggers the panel instead.
3. When detected, it calls Arctic Shift's `/api/posts/search?author=<name>` and `/api/comments/search?author=<name>` ([src/arctic-shift.js](src/arctic-shift.js))
4. Results are rendered in a `.ru-panel` styled by [src/styles.css](src/styles.css). Each section loads up to 100 items; a **Load older** button pages further back through the archive (`before=<created_utc>` cursor).

Only what's hidden is fetched. If only comments are hidden, only comments are loaded. If both are hidden, both are loaded.

## Deleted & removed content in threads

Inside a thread (`/r/<sub>/comments/<id>/…`), the extension also spots posts and comments
that show up as `[deleted]` / `[removed]` / "Comment removed by moderator" and adds a small
**Reveal archived** button beside each one ([src/thread.js](src/thread.js)). Click it and the
original author and body are fetched from Arctic Shift and rendered in place:

- Comments → `/api/comments/ids?ids=<id>`
- Posts → `/api/posts/ids?ids=<id>` (falls back to the original link URL for non-text posts)

Nothing is fetched until you click, so prolific threads don't trigger bulk requests. Newly
loaded comments (from scrolling or "view more comments") get buttons automatically via a
`MutationObserver`. Works on both the current Reddit UI (`shreddit-*` elements) and old
Reddit's markup (`.thing` / `.usertext-body`).

## Permissions

- Content script runs on `www.reddit.com`, `sh.reddit.com`, and `old.reddit.com` (via the manifest's `content_scripts.matches` — no broader page access).
- One host permission: `https://arctic-shift.photon-reddit.com/*`, used to fetch archived posts/comments. Without it, MV3 blocks the cross-origin request.

No `tabs`, `storage`, `cookies`, or other Chrome APIs are requested.

## Limitations

- **Archive coverage**: Content deleted within minutes of being posted may not be in Arctic Shift.
- **Page size**: 100 posts/comments per request (Arctic Shift's per-query maximum). Use the **Load older** button in each section to page further back.
- **Old Reddit detection**: old Reddit has no "hidden profile" notice, so any empty profile listing offers the archive panel — including profiles that are genuinely empty (the panel will simply report that the archive has nothing).

## Files

```
manifest.json           MV3 manifest
src/arctic-shift.js     Arctic Shift API client (cached, deduped, paginated)
src/dom.js              DOM helpers
src/profile.js          Hidden-profile detection + render + pagination
src/thread.js           In-thread deleted/removed reveal (new + old Reddit)
src/main.js             SPA navigation router
src/styles.css          Panel styles
src/popup.html          Toolbar popup (lookup-by-username shortcut)
src/popup.js
icons/                  Toolbar icons
store-assets/           Chrome Web Store listing images (generate.py)
```
