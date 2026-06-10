"""Composite the raw popup capture onto a 1280x800 store-screenshot frame."""
import io
from pathlib import Path

import cairosvg
from PIL import Image

HERE = Path(__file__).parent
POPUP_PATH = HERE / "Capture.PNG"
OUT = HERE / "screenshot-4-popup-1280x800.png"

W, H = 1280, 800
BG_DEEP_RGB = (15, 16, 18)

# Where to land the popup on the canvas
popup = Image.open(POPUP_PATH).convert("RGBA")
# The raw capture ends mid-line; crop the partial text row off the bottom.
popup = popup.crop((0, 0, popup.size[0], popup.size[1] - 18))
# Scale the popup up so it reads better at viewing size (still well below 1280x800)
SCALE = 1.6
PW, PH = int(popup.size[0] * SCALE), int(popup.size[1] * SCALE)
popup = popup.resize((PW, PH), Image.LANCZOS)

# Toolbar icon position (pinned to right side of stylized browser chrome)
TOOLBAR_Y = 170
TOOLBAR_H = 60
ICON_CX = 940  # x-center of the pinned icon
POPUP_X = ICON_CX - PW + 30  # popup sits just to the left of icon, like Chrome does
POPUP_Y = TOOLBAR_Y + TOOLBAR_H + 14

bg_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="brand" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FF6A2A"/>
      <stop offset="1" stop-color="#E03A0B"/>
    </linearGradient>
    <linearGradient id="brandH" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#FF6A2A"/>
      <stop offset="1" stop-color="#E03A0B"/>
    </linearGradient>
    <radialGradient id="bgGlow" cx="20%" cy="20%" r="80%">
      <stop offset="0" stop-color="#3A1A0C" stop-opacity="0.9"/>
      <stop offset="0.6" stop-color="#0F1012" stop-opacity="1"/>
      <stop offset="1" stop-color="#06070A" stop-opacity="1"/>
    </radialGradient>
    <radialGradient id="iconGlow" cx="50%" cy="50%" r="60%">
      <stop offset="0" stop-color="#FF6A2A" stop-opacity="0.45"/>
      <stop offset="1" stop-color="#FF6A2A" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

  <!-- headline -->
  <text x="{W/2}" y="78" text-anchor="middle"
        font-family="DejaVu Sans, Liberation Sans, sans-serif"
        font-size="30" font-weight="800" fill="#F2F2F3" letter-spacing="-0.5">
    One-click lookup from the toolbar
  </text>
  <text x="{W/2}" y="112" text-anchor="middle"
        font-family="DejaVu Sans, Liberation Sans, sans-serif"
        font-size="15" fill="#9A9A9C">
    Type any username and jump straight to their profile — no search bar, no sign-in.
  </text>

  <!-- stylized browser toolbar strip -->
  <rect x="80" y="{TOOLBAR_Y}" width="{W - 160}" height="{TOOLBAR_H}" rx="12" fill="#202021" stroke="#3A3A3C"/>
  <!-- traffic lights -->
  <circle cx="106" cy="{TOOLBAR_Y + TOOLBAR_H / 2}" r="6" fill="#FF5F57"/>
  <circle cx="126" cy="{TOOLBAR_Y + TOOLBAR_H / 2}" r="6" fill="#FEBC2E"/>
  <circle cx="146" cy="{TOOLBAR_Y + TOOLBAR_H / 2}" r="6" fill="#28C840"/>
  <!-- url bar -->
  <rect x="184" y="{TOOLBAR_Y + 16}" width="680" height="28" rx="14" fill="#0F0F10" stroke="#3A3A3C"/>
  <text x="206" y="{TOOLBAR_Y + 34}" font-family="DejaVu Sans Mono, monospace"
        font-size="12" fill="#9A9A9C">reddit.com</text>

  <!-- pinned extension icon (highlighted) -->
  <circle cx="{ICON_CX}" cy="{TOOLBAR_Y + TOOLBAR_H / 2}" r="34" fill="url(#iconGlow)"/>
  <g transform="translate({ICON_CX - 18}, {TOOLBAR_Y + TOOLBAR_H / 2 - 18})">
    <rect width="36" height="36" rx="8" fill="url(#brand)"/>
    <path d="M 4 18 Q 18 4 32 18 Q 18 32 4 18 Z" fill="#fdfdfd"/>
    <circle cx="18" cy="18" r="7" fill="#15171c"/>
    <circle cx="18" cy="18" r="3.4" fill="#000"/>
    <circle cx="16" cy="16" r="1.6" fill="#fff"/>
  </g>

  <!-- subtle caret connecting toolbar icon to popup (drawn so it lands under the popup top edge) -->
  <path d="M {ICON_CX} {TOOLBAR_Y + TOOLBAR_H + 2}
           L {ICON_CX - 9} {TOOLBAR_Y + TOOLBAR_H + 14}
           L {ICON_CX + 9} {TOOLBAR_Y + TOOLBAR_H + 14} Z"
        fill="#1A1A1B" stroke="#3A3A3C"/>

  <!-- soft drop shadow for the popup (rendered behind the pasted PNG) -->
  <rect x="{POPUP_X - 10}" y="{POPUP_Y + 8}" width="{PW + 20}" height="{PH + 16}" rx="14"
        fill="#000" fill-opacity="0.55"/>

  <!-- annotation arrow + label, pointing at the popup's input field -->
  <g>
    <rect x="180" y="{POPUP_Y + 80}" width="280" height="48" rx="24"
          fill="#1A1A1B" stroke="url(#brandH)" stroke-width="1.5"/>
    <text x="320" y="{POPUP_Y + 110}" text-anchor="middle"
          font-family="DejaVu Sans, Liberation Sans, sans-serif"
          font-size="15" font-weight="700" fill="#F2F2F3">
      Type a username, hit Go
    </text>
    <path d="M 460 {POPUP_Y + 104} Q 560 {POPUP_Y + 140} {POPUP_X + 60} {POPUP_Y + PH - 70}"
          stroke="url(#brandH)" stroke-width="2.5" fill="none"
          stroke-linecap="round" stroke-dasharray="6 6"/>
    <circle cx="{POPUP_X + 60}" cy="{POPUP_Y + PH - 70}" r="5" fill="url(#brandH)"/>
  </g>

  <!-- bottom feature chips -->
  <g font-family="DejaVu Sans, Liberation Sans, sans-serif" font-size="14" font-weight="700" fill="#F2F2F3">
    <g>
      <rect x="295" y="700" width="170" height="42" rx="21" fill="#1A1A1B" stroke="#3A3A3C"/>
      <text x="380" y="727" text-anchor="middle">No sign-in</text>
    </g>
    <g>
      <rect x="485" y="700" width="170" height="42" rx="21" fill="#1A1A1B" stroke="#3A3A3C"/>
      <text x="570" y="727" text-anchor="middle">No tracking</text>
    </g>
    <g>
      <rect x="675" y="700" width="170" height="42" rx="21" fill="#1A1A1B" stroke="#3A3A3C"/>
      <text x="760" y="727" text-anchor="middle">No analytics</text>
    </g>
    <g>
      <rect x="865" y="700" width="170" height="42" rx="21" fill="#1A1A1B" stroke="#3A3A3C"/>
      <text x="950" y="727" text-anchor="middle">Manifest V3</text>
    </g>
  </g>
</svg>"""

bg_png = cairosvg.svg2png(bytestring=bg_svg.encode("utf-8"), output_width=W, output_height=H)
canvas = Image.open(io.BytesIO(bg_png)).convert("RGBA")

# Paste the real popup capture
canvas.paste(popup, (POPUP_X, POPUP_Y), popup)

# Flatten to 24-bit RGB (no alpha)
flat = Image.new("RGB", canvas.size, BG_DEEP_RGB)
flat.paste(canvas, mask=canvas.split()[3])
flat.save(OUT, "PNG", optimize=True)
print(f"wrote {OUT.name}  ({flat.size[0]}x{flat.size[1]}, mode={flat.mode})")
