"""Render Chrome Web Store listing assets from inline SVGs.

Produces 24-bit PNGs (no alpha) at the exact dimensions the store requires.
Run: python3 generate.py
"""
import io
from pathlib import Path

import cairosvg
from PIL import Image

OUT = Path(__file__).parent

# ---- shared palette ----
ORANGE_LIGHT = "#FF6A2A"
ORANGE_DARK = "#E03A0B"
BG_DEEP = "#0F1012"
BG_SURFACE = "#1A1A1B"
BG_PANEL = "#272729"
BG_PANEL_HI = "#2F2F31"
BORDER = "#3A3A3C"
TEXT_HI = "#F2F2F3"
TEXT_MID = "#D7DADC"
TEXT_LOW = "#9A9A9C"
ACCENT_HIDDEN = "#FFB020"


def shared_defs() -> str:
    return f"""
    <defs>
      <linearGradient id="brand" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="{ORANGE_LIGHT}"/>
        <stop offset="1" stop-color="{ORANGE_DARK}"/>
      </linearGradient>
      <linearGradient id="brandH" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="{ORANGE_LIGHT}"/>
        <stop offset="1" stop-color="{ORANGE_DARK}"/>
      </linearGradient>
      <radialGradient id="bgGlow" cx="20%" cy="20%" r="80%">
        <stop offset="0" stop-color="#3A1A0C" stop-opacity="0.9"/>
        <stop offset="0.6" stop-color="{BG_DEEP}" stop-opacity="1"/>
        <stop offset="1" stop-color="#06070A" stop-opacity="1"/>
      </radialGradient>
      <radialGradient id="iris" cx="50%" cy="42%" r="58%">
        <stop offset="0" stop-color="#3a3f4a"/>
        <stop offset="0.7" stop-color="#15171c"/>
        <stop offset="1" stop-color="#000"/>
      </radialGradient>
      <linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#fff" stop-opacity="0.18"/>
        <stop offset="0.55" stop-color="#fff" stop-opacity="0"/>
      </linearGradient>
      <filter id="iconShadow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceAlpha" stdDeviation="6"/>
        <feOffset dx="0" dy="4"/>
        <feComponentTransfer><feFuncA type="linear" slope="0.55"/></feComponentTransfer>
        <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    """


def app_icon(cx: float, cy: float, size: float, shadow: bool = True) -> str:
    """Render the extension icon centered at (cx, cy)."""
    s = size
    x = cx - s / 2
    y = cy - s / 2
    r = s * (28 / 128)
    eye_left = x + s * (14 / 128)
    eye_right = x + s * (114 / 128)
    eye_mid_y = y + s * (64 / 128)
    iris_r = s * (26 / 128)
    pupil_r = s * (12 / 128)
    cl_r = s * (5.5 / 128)
    filt = 'filter="url(#iconShadow)"' if shadow else ""
    return f"""
    <g {filt}>
      <rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{r}" ry="{r}" fill="url(#brand)"/>
      <rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{r}" ry="{r}" fill="url(#sheen)"/>
      <path d="M {eye_left} {eye_mid_y}
               Q {cx} {y + s * (14 / 128)} {eye_right} {eye_mid_y}
               Q {cx} {y + s * (114 / 128)} {eye_left} {eye_mid_y} Z"
            fill="#fdfdfd"/>
      <circle cx="{cx}" cy="{eye_mid_y}" r="{iris_r}" fill="url(#iris)"/>
      <circle cx="{cx}" cy="{eye_mid_y}" r="{pupil_r}" fill="#000"/>
      <circle cx="{cx - s * (8/128)}" cy="{eye_mid_y - s * (8/128)}" r="{cl_r}" fill="#fff" opacity="0.95"/>
      <path d="M {x + s * (16/128)} {eye_mid_y}
               Q {cx} {y + s * (16/128)} {x + s * (112/128)} {eye_mid_y}"
            fill="none" stroke="#000" stroke-opacity="0.16"
            stroke-width="{s * (2.5/128)}" stroke-linecap="round"/>
    </g>
    """


def render(svg: str, w: int, h: int, out_path: Path) -> None:
    """Rasterize SVG and flatten to 24-bit (RGB, no alpha) PNG."""
    png_bytes = cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        output_width=w,
        output_height=h,
    )
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    flat = Image.new("RGB", img.size, (15, 16, 18))  # BG_DEEP, must match design
    flat.paste(img, mask=img.split()[3])
    flat.save(out_path, "PNG", optimize=True)
    print(f"  wrote {out_path.name}  ({flat.size[0]}x{flat.size[1]}, mode={flat.mode})")


# ----------------------------------------------------------------------
# 1) Small promo tile — 440x280
# ----------------------------------------------------------------------
def small_promo() -> str:
    W, H = 440, 280
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>
      <!-- subtle grid of dots -->
      <g fill="#FFFFFF" fill-opacity="0.04">
        {"".join(f'<circle cx="{x}" cy="{y}" r="1.2"/>' for x in range(20, W, 28) for y in range(20, H, 28))}
      </g>
      {app_icon(110, 140, 150)}
      <text x="208" y="118" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="26" font-weight="800" fill="{TEXT_HI}" letter-spacing="-0.4">Reddit Profile</text>
      <text x="208" y="148" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="26" font-weight="800" fill="url(#brandH)" letter-spacing="-0.4">Unhider</text>
      <text x="208" y="184" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="13" font-weight="500" fill="{TEXT_MID}">Reveal hidden posts</text>
      <text x="208" y="202" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="13" font-weight="500" fill="{TEXT_MID}">&amp; comments — automatically.</text>
      <rect x="208" y="222" width="166" height="28" rx="14" fill="url(#brandH)"/>
      <text x="291" y="241" text-anchor="middle"
            font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="11" font-weight="700" fill="#fff" letter-spacing="0.6">NO TRACKING · MV3</text>
    </svg>"""


# ----------------------------------------------------------------------
# 2) Marquee promo tile — 1400x560
# ----------------------------------------------------------------------
def marquee_promo() -> str:
    W, H = 1400, 560
    # right side: before/after card mock
    card_x = 860
    card_y = 100
    card_w = 480
    card_h = 360
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>
      <g fill="#FFFFFF" fill-opacity="0.035">
        {"".join(f'<circle cx="{x}" cy="{y}" r="1.4"/>' for x in range(30, W, 36) for y in range(30, H, 36))}
      </g>

      <!-- LEFT: icon + headline -->
      {app_icon(140, 220, 200)}
      <text x="260" y="200" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="46" font-weight="800" fill="{TEXT_HI}" letter-spacing="-1.2">Reddit Profile</text>
      <text x="260" y="250" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="46" font-weight="800" fill="url(#brandH)" letter-spacing="-1.2">Unhider</text>
      <text x="260" y="298" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="18" font-weight="500" fill="{TEXT_MID}">See posts &amp; comments hidden on a user's</text>
      <text x="260" y="322" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="18" font-weight="500" fill="{TEXT_MID}">profile — pulled from the public archive,</text>
      <text x="260" y="346" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="18" font-weight="500" fill="{TEXT_MID}">automatically.</text>

      <!-- feature chips -->
      <g font-family="DejaVu Sans, Liberation Sans, sans-serif" font-size="13" font-weight="700" fill="{TEXT_HI}">
        <g>
          <rect x="260" y="400" width="140" height="36" rx="18" fill="{BG_PANEL}" stroke="{BORDER}"/>
          <text x="330" y="423" text-anchor="middle">Zero clicks</text>
        </g>
        <g>
          <rect x="412" y="400" width="140" height="36" rx="18" fill="{BG_PANEL}" stroke="{BORDER}"/>
          <text x="482" y="423" text-anchor="middle">No tracking</text>
        </g>
        <g>
          <rect x="564" y="400" width="140" height="36" rx="18" fill="{BG_PANEL}" stroke="{BORDER}"/>
          <text x="634" y="423" text-anchor="middle">Manifest V3</text>
        </g>
      </g>

      <!-- RIGHT: mock card showing before/after -->
      <g>
        <rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="14"
              fill="{BG_SURFACE}" stroke="{BORDER}"/>
        <!-- hidden notice -->
        <rect x="{card_x + 24}" y="{card_y + 28}" width="{card_w - 48}" height="64" rx="8"
              fill="{BG_PANEL}" stroke="{BORDER}"/>
        <circle cx="{card_x + 56}" cy="{card_y + 60}" r="14" fill="{ACCENT_HIDDEN}" fill-opacity="0.18"/>
        <text x="{card_x + 56}" y="{card_y + 66}" text-anchor="middle"
              font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="18" font-weight="800" fill="{ACCENT_HIDDEN}">!</text>
        <text x="{card_x + 84}" y="{card_y + 56}" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="13" font-weight="700" fill="{TEXT_HI}">u/example likes to keep their posts hidden</text>
        <text x="{card_x + 84}" y="{card_y + 76}" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="12" fill="{TEXT_LOW}">…but the archive remembers.</text>

        <!-- arrow -->
        <g transform="translate({card_x + card_w / 2 - 14}, {card_y + 112})">
          <circle cx="14" cy="14" r="14" fill="url(#brandH)"/>
          <path d="M 9 14 L 19 14 M 15 10 L 19 14 L 15 18" stroke="#fff" stroke-width="2"
                fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </g>

        <!-- panel header -->
        <text x="{card_x + 24}" y="{card_y + 170}" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="11" font-weight="700" fill="url(#brandH)" letter-spacing="1.6">RECOVERED · 47 POSTS</text>

        <!-- mock posts -->
        {"".join(post_row(card_x + 24, card_y + 184 + i * 46, card_w - 48, title, sub)
                 for i, (title, sub) in enumerate([
                     ("Anyone else's CRT make this sound on cold mornings?", "r/retrogaming · 312 pts"),
                     ("Built a tiny CLI for managing GPG keys", "r/programming · 1.2k pts"),
                     ("Sourdough starter died — autopsy thread", "r/Breadit · 88 pts"),
                 ]))}
      </g>
    </svg>"""


def post_row(x: float, y: float, w: float, title: str, sub: str) -> str:
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="38" rx="6" fill="{BG_PANEL}"/>
      <rect x="{x}" y="{y}" width="3" height="38" rx="1.5" fill="url(#brand)"/>
      <text x="{x + 14}" y="{y + 17}" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="13" font-weight="700" fill="{TEXT_HI}">{title}</text>
      <text x="{x + 14}" y="{y + 31}" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="11" fill="{TEXT_LOW}">{sub}</text>
    """


# ----------------------------------------------------------------------
# 3) Screenshot — "before & after" hero (1280x800)
# ----------------------------------------------------------------------
def screenshot_before_after() -> str:
    W, H = 1280, 800
    # browser frame
    frame_x, frame_y = 80, 70
    frame_w, frame_h = W - 160, H - 140
    chrome_h = 44
    content_x = frame_x + 24
    content_y = frame_y + chrome_h + 28
    content_w = frame_w - 48

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

      <!-- top headline -->
      <text x="{W/2}" y="50" text-anchor="middle"
            font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="22" font-weight="700" fill="{TEXT_HI}">
        Hidden profile? The extension fills it back in — automatically.
      </text>

      <!-- browser frame -->
      <rect x="{frame_x}" y="{frame_y}" width="{frame_w}" height="{frame_h}" rx="12"
            fill="{BG_SURFACE}" stroke="{BORDER}"/>
      <rect x="{frame_x}" y="{frame_y}" width="{frame_w}" height="{chrome_h}" rx="12"
            fill="#202021"/>
      <rect x="{frame_x}" y="{frame_y + chrome_h - 12}" width="{frame_w}" height="12" fill="#202021"/>
      <!-- traffic lights -->
      <circle cx="{frame_x + 22}" cy="{frame_y + chrome_h/2}" r="6" fill="#FF5F57"/>
      <circle cx="{frame_x + 40}" cy="{frame_y + chrome_h/2}" r="6" fill="#FEBC2E"/>
      <circle cx="{frame_x + 58}" cy="{frame_y + chrome_h/2}" r="6" fill="#28C840"/>
      <!-- url bar -->
      <rect x="{frame_x + 92}" y="{frame_y + 10}" width="{frame_w - 184}" height="24" rx="12"
            fill="#0F0F10" stroke="{BORDER}"/>
      <text x="{frame_x + 108}" y="{frame_y + 27}" font-family="DejaVu Sans Mono, monospace"
            font-size="11" fill="{TEXT_LOW}">reddit.com/user/example/</text>
      <!-- extension icon pinned -->
      <g transform="translate({frame_x + frame_w - 70}, {frame_y + 10})">
        {app_icon(12, 12, 24, shadow=False)}
      </g>

      <!-- avatar + username -->
      <circle cx="{content_x + 32}" cy="{content_y + 28}" r="26" fill="url(#brand)"/>
      <text x="{content_x + 32}" y="{content_y + 34}" text-anchor="middle"
            font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="22" font-weight="800" fill="#fff">e</text>
      <text x="{content_x + 70}" y="{content_y + 24}" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="22" font-weight="800" fill="{TEXT_HI}">u/example</text>
      <text x="{content_x + 70}" y="{content_y + 44}" font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="12" fill="{TEXT_LOW}">3y · 12.4k karma</text>

      <!-- the hidden notice -->
      <g transform="translate({content_x}, {content_y + 80})">
        <rect width="{content_w}" height="64" rx="10" fill="{BG_PANEL}" stroke="{BORDER}"/>
        <circle cx="36" cy="32" r="16" fill="{ACCENT_HIDDEN}" fill-opacity="0.16"/>
        <text x="36" y="38" text-anchor="middle" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="20" font-weight="800" fill="{ACCENT_HIDDEN}">!</text>
        <text x="66" y="28" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="14" font-weight="700" fill="{TEXT_HI}">
          u/example likes to keep their posts hidden,
        </text>
        <text x="66" y="48" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="13" fill="{TEXT_LOW}">
          but check out their stats to learn more about them.
        </text>
      </g>

      <!-- arrow callout (inside the frame, to the right of the hidden notice) -->
      <g transform="translate({content_x + content_w - 110}, {content_y + 112})">
        <rect x="-6" y="-14" width="116" height="28" rx="14" fill="{ACCENT_HIDDEN}" fill-opacity="0.12"
              stroke="{ACCENT_HIDDEN}" stroke-opacity="0.45"/>
        <circle cx="6" cy="0" r="4" fill="{ACCENT_HIDDEN}"/>
        <text x="20" y="5" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="12" font-weight="800" fill="{ACCENT_HIDDEN}" letter-spacing="0.8">DETECTED</text>
      </g>

      <!-- the panel injected by the extension -->
      <g transform="translate({content_x}, {content_y + 168})">
        <rect width="{content_w}" height="370" rx="12" fill="{BG_PANEL}" stroke="url(#brandH)" stroke-width="1.5"/>
        <!-- panel header -->
        <rect width="{content_w}" height="44" rx="12" fill="{BG_PANEL_HI}"/>
        <rect y="32" width="{content_w}" height="12" fill="{BG_PANEL_HI}"/>
        <g transform="translate(16, 12)">
          {app_icon(10, 10, 20, shadow=False)}
        </g>
        <text x="42" y="28" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="13" font-weight="800" fill="{TEXT_HI}">Reddit Profile Unhider</text>
        <text x="{content_w - 16}" y="28" text-anchor="end"
              font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="11" font-weight="700" fill="url(#brandH)" letter-spacing="1.4">
          47 POSTS · 132 COMMENTS RECOVERED
        </text>

        <!-- tabs -->
        <g transform="translate(16, 56)">
          <rect width="100" height="28" rx="14" fill="url(#brandH)"/>
          <text x="50" y="18" text-anchor="middle"
                font-family="DejaVu Sans, Liberation Sans, sans-serif"
                font-size="12" font-weight="800" fill="#fff">Posts</text>
          <text x="140" y="18" font-family="DejaVu Sans, Liberation Sans, sans-serif"
                font-size="12" font-weight="700" fill="{TEXT_LOW}">Comments</text>
        </g>

        <!-- post list -->
        {"".join(big_post_row(16, 100 + i * 56, content_w - 32, title, sub)
                 for i, (title, sub) in enumerate([
                     ("Anyone else's CRT make a high-pitched whine on cold mornings?", "r/retrogaming · 312 pts · 2y ago"),
                     ("Built a tiny CLI for managing GPG keys across machines", "r/programming · 1.2k pts · 1y ago"),
                     ("Sourdough starter died after 4 years — full autopsy thread", "r/Breadit · 88 pts · 8mo ago"),
                     ("TIL: Java's Object.hashCode is not guaranteed across JVMs", "r/learnprogramming · 540 pts · 6mo ago"),
                 ]))}
      </g>
    </svg>"""


def big_post_row(x: float, y: float, w: float, title: str, sub: str) -> str:
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="48" rx="8" fill="{BG_PANEL_HI}"/>
        <rect width="4" height="48" rx="2" fill="url(#brand)"/>
        <text x="18" y="22" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="14" font-weight="700" fill="{TEXT_HI}">{title}</text>
        <text x="18" y="40" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="11" fill="{TEXT_LOW}">{sub}</text>
        <text x="{w - 16}" y="30" text-anchor="end"
              font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="11" font-weight="700" fill="url(#brandH)">open ↗</text>
      </g>
    """


# ----------------------------------------------------------------------
# 4) Screenshot — "comments panel" (1280x800)
# ----------------------------------------------------------------------
def screenshot_comments() -> str:
    W, H = 1280, 800
    panel_x = 140
    panel_y = 130
    panel_w = W - 280
    panel_h = H - 200

    comments = [
        ("Honestly the whine is the flyback transformer aging — once it starts you can't un-hear it. Replacing the cap pack on the chassis helped mine but the whine never fully went away.",
         "r/retrogaming · 84 pts · 2y ago"),
        ("If you're already on GPG you might also like passage — it's age under the hood but uses a pass-like layout. Way faster than the GPG agent on slow boxes.",
         "r/linux · 41 pts · 1y ago"),
        ("Yeah, you basically need to keep at least two starters going if you care. I lost mine to a fridge that ran a degree too warm for a week — no symptoms until day 5.",
         "r/Breadit · 19 pts · 8mo ago"),
        ("This is also why you shouldn't lean on hashCode for cross-process keying. If you need that, use a hash function with a stable spec — SHA-256, xxhash, whatever fits.",
         "r/learnprogramming · 220 pts · 6mo ago"),
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

      <text x="{W/2}" y="60" text-anchor="middle"
            font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="22" font-weight="700" fill="{TEXT_HI}">
        Hidden comments too — pulled from the public archive.
      </text>
      <text x="{W/2}" y="90" text-anchor="middle"
            font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="14" fill="{TEXT_LOW}">
        Each one links back to the original thread. No login. No tracking.
      </text>

      <g transform="translate({panel_x}, {panel_y})">
        <rect width="{panel_w}" height="{panel_h}" rx="14" fill="{BG_SURFACE}"
              stroke="url(#brandH)" stroke-width="1.5"/>
        <!-- header -->
        <rect width="{panel_w}" height="56" rx="14" fill="{BG_PANEL}"/>
        <rect y="42" width="{panel_w}" height="14" fill="{BG_PANEL}"/>
        <g transform="translate(20, 16)">
          {app_icon(12, 12, 24, shadow=False)}
        </g>
        <text x="54" y="36" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="15" font-weight="800" fill="{TEXT_HI}">Reddit Profile Unhider</text>

        <!-- tabs -->
        <g transform="translate(20, 76)">
          <rect width="110" height="32" rx="16" fill="{BG_PANEL}" stroke="{BORDER}"/>
          <text x="55" y="20" text-anchor="middle" font-family="DejaVu Sans, Liberation Sans, sans-serif"
                font-size="13" font-weight="700" fill="{TEXT_LOW}">Posts (47)</text>
          <g transform="translate(122, 0)">
            <rect width="160" height="32" rx="16" fill="url(#brandH)"/>
            <text x="80" y="20" text-anchor="middle" font-family="DejaVu Sans, Liberation Sans, sans-serif"
                  font-size="13" font-weight="800" fill="#fff">Comments (132)</text>
          </g>
        </g>

        <!-- comment cards -->
        {"".join(comment_card(20, 130 + i * 120, panel_w - 40, body, meta)
                 for i, (body, meta) in enumerate(comments))}
      </g>
    </svg>"""


def comment_card(x: float, y: float, w: float, body: str, meta: str) -> str:
    # Wrap body manually — cairosvg doesn't honor CSS wrapping. Split into two lines.
    words = body.split()
    line1, line2 = [], []
    target = len(body) // 2
    cur = 0
    for word in words:
        if cur < target:
            line1.append(word)
            cur += len(word) + 1
        else:
            line2.append(word)
    line1_s = " ".join(line1)
    line2_s = " ".join(line2)
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="100" rx="10" fill="{BG_PANEL}"/>
        <rect width="4" height="100" rx="2" fill="url(#brand)"/>
        <text x="20" y="32" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="14" fill="{TEXT_HI}">{escape(line1_s)}</text>
        <text x="20" y="56" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="14" fill="{TEXT_HI}">{escape(line2_s)}</text>
        <text x="20" y="82" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="12" font-weight="700" fill="{TEXT_LOW}">{escape(meta)}</text>
        <text x="{w - 16}" y="82" text-anchor="end"
              font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="12" font-weight="700" fill="url(#brandH)">view thread ↗</text>
      </g>
    """


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;")


# ----------------------------------------------------------------------
# 5) Screenshot — "how it works" (1280x800)
# ----------------------------------------------------------------------
def screenshot_how() -> str:
    W, H = 1280, 800
    steps = [
        ("1", "Open a profile", "Visit any reddit.com/user/<name> page."),
        ("2", "Detect the notice", "A MutationObserver catches the 'likes to keep their posts hidden' banner."),
        ("3", "Archive fetch", "Posts & comments are pulled from the public Arctic Shift mirror."),
        ("4", "Render inline", "A panel slots in right below the notice — no clicks, no popups."),
    ]
    cell_w = 280
    cell_gap = 24
    total = len(steps) * cell_w + (len(steps) - 1) * cell_gap
    start_x = (W - total) / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

      <text x="{W/2}" y="100" text-anchor="middle"
            font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="34" font-weight="800" fill="{TEXT_HI}" letter-spacing="-0.6">How it works</text>
      <text x="{W/2}" y="138" text-anchor="middle"
            font-family="DejaVu Sans, Liberation Sans, sans-serif"
            font-size="16" fill="{TEXT_LOW}">
        One content script. One host permission. No background workers, no storage, no tracking.
      </text>

      {"".join(step_card(start_x + i * (cell_w + cell_gap), 220, cell_w, num, title, body)
               for i, (num, title, body) in enumerate(steps))}

      <!-- footer privacy strip -->
      <g transform="translate({W/2 - 380}, 660)">
        <rect width="760" height="80" rx="14" fill="{BG_SURFACE}" stroke="{BORDER}"/>
        <text x="380" y="36" text-anchor="middle"
              font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="14" font-weight="800" fill="{TEXT_HI}" letter-spacing="0.4">
          PERMISSIONS
        </text>
        <text x="380" y="60" text-anchor="middle"
              font-family="DejaVu Sans Mono, monospace"
              font-size="13" fill="{TEXT_MID}">
          arctic-shift.photon-reddit.com  ·  www.reddit.com  ·  sh.reddit.com
        </text>
      </g>
    </svg>"""


def step_card(x: float, y: float, w: float, num: str, title: str, body: str) -> str:
    # naive wrap for body
    words = body.split()
    lines, cur = [], ""
    for word in words:
        candidate = (cur + " " + word).strip()
        if len(candidate) > 32 and cur:
            lines.append(cur)
            cur = word
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    line_svg = "".join(
        f'<text x="20" y="{160 + i*20}" font-family="DejaVu Sans, Liberation Sans, sans-serif" '
        f'font-size="13" fill="{TEXT_MID}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="320" rx="14" fill="{BG_SURFACE}" stroke="{BORDER}"/>
        <circle cx="56" cy="56" r="32" fill="url(#brand)"/>
        <text x="56" y="68" text-anchor="middle"
              font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="30" font-weight="800" fill="#fff">{escape(num)}</text>
        <text x="20" y="124" font-family="DejaVu Sans, Liberation Sans, sans-serif"
              font-size="18" font-weight="800" fill="{TEXT_HI}">{escape(title)}</text>
        {line_svg}
      </g>
    """


def main() -> None:
    print("rendering store assets …")
    render(small_promo(), 440, 280, OUT / "promo-small-440x280.png")
    render(marquee_promo(), 1400, 560, OUT / "promo-marquee-1400x560.png")
    render(screenshot_before_after(), 1280, 800, OUT / "screenshot-1-hero-1280x800.png")
    render(screenshot_comments(), 1280, 800, OUT / "screenshot-2-comments-1280x800.png")
    render(screenshot_how(), 1280, 800, OUT / "screenshot-3-howitworks-1280x800.png")
    print("done.")


if __name__ == "__main__":
    main()
