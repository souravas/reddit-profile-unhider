# Store Listings — URLs

Dashboard fields to paste into the Chrome Web Store Developer Dashboard and the
Firefox Add-ons Developer Hub when publishing Reddit Profile Unhider. The store
description itself lives in [description.txt](description.txt).

## Homepage URL

```
https://github.com/souravas/reddit-profile-unhider
```

## Support URL

```
https://github.com/souravas/reddit-profile-unhider/issues
```

## Privacy policy URL

```
https://github.com/souravas/reddit-profile-unhider/blob/main/PRIVACY.md
```

## Firefox Add-ons notes

- **Upload**: the zip from the README's Packaging section. The code isn't minified or bundled, so no source code submission is needed.
- **Add-on ID**: `reddit-profile-unhider@souravas.github.io` (`browser_specific_settings.gecko.id`). The first upload claims it for this listing, and every later version must keep it.
- **Data collection**: the manifest declares **browsing activity** as required, since the viewed profile's username, or a revealed post/comment's ID, is sent to Arctic Shift. Firefox shows this in the install prompt.
- **Platforms**: desktop Firefox 140 or later. Firefox for Android isn't enabled (the manifest has no `gecko_android` key).
