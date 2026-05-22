# Privacy Policy — Reddit Profile Unhider

Reddit Profile Unhider does not collect, store, transmit, sell, or share any personal information about its users.

## What the extension does

- Runs only on `reddit.com` and `sh.reddit.com` user profile pages.
- When a profile shows the "user has hidden their posts/comments" notice, the extension sends the Reddit username visible in the URL to the public Arctic Shift archive (`https://arctic-shift.photon-reddit.com`) to retrieve that user's publicly archived posts and comments, and renders them inline in the page.
- The toolbar popup accepts a Reddit username and opens `https://www.reddit.com/user/<name>/` in a new tab. The username is not transmitted anywhere by the popup itself.

## Data collection

- No personally identifiable information is collected.
- No browsing history, page content, clicks, keystrokes, location, or credentials are collected, stored, or transmitted.
- No analytics, tracking, advertising, or third-party SDKs are included.
- No data is stored locally beyond an in-memory request cache for the current page, which is cleared when the tab is closed.

## Third-party requests

The extension makes HTTPS requests to `https://arctic-shift.photon-reddit.com` solely to fetch publicly archived Reddit content. Only the Reddit username being viewed (not any data about the extension's user) is included in the request. Arctic Shift's own data handling is governed by its operators.

## Permissions

- **Host permission** `https://arctic-shift.photon-reddit.com/*` — required by Manifest V3 to make the cross-origin fetch above.
- **Content script matches** `https://www.reddit.com/*` and `https://sh.reddit.com/*` — required so the extension can detect the hidden-profile notice and render results in the page.

The extension does not request `tabs`, `storage`, `cookies`, `webRequest`, `identity`, or any other Chrome API permissions.

## Changes to this policy

If the extension's data practices ever change, this document will be updated and the extension's Chrome Web Store listing will reflect the new disclosures.

## Contact

Questions or concerns: souravas007@gmail.com
