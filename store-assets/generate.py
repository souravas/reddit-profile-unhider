"""Render Chrome Web Store listing assets from inline SVGs.

Produces 24-bit PNGs (no alpha) at the exact dimensions the store requires.
The mocked panel/buttons mirror the real injected UI (src/styles.css) so the
listing matches what users actually see.

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

FONT = "DejaVu Sans, Liberation Sans, sans-serif"
MONO = "DejaVu Sans Mono, monospace"


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;")


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
# shared building blocks
# ----------------------------------------------------------------------
def browser_frame(x: float, y: float, w: float, h: float, url: str) -> str:
    """macOS-style browser chrome with the extension icon pinned top-right."""
    chrome_h = 44
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{BG_SURFACE}" stroke="{BORDER}"/>
      <rect x="{x}" y="{y}" width="{w}" height="{chrome_h}" rx="12" fill="#202021"/>
      <rect x="{x}" y="{y + chrome_h - 12}" width="{w}" height="12" fill="#202021"/>
      <circle cx="{x + 22}" cy="{y + chrome_h/2}" r="6" fill="#FF5F57"/>
      <circle cx="{x + 40}" cy="{y + chrome_h/2}" r="6" fill="#FEBC2E"/>
      <circle cx="{x + 58}" cy="{y + chrome_h/2}" r="6" fill="#28C840"/>
      <rect x="{x + 92}" y="{y + 10}" width="{w - 184}" height="24" rx="12"
            fill="#0F0F10" stroke="{BORDER}"/>
      <text x="{x + 108}" y="{y + 27}" font-family="{MONO}" font-size="11" fill="{TEXT_LOW}">{escape(url)}</text>
      <g transform="translate({x + w - 70}, {y + 10})">
        {app_icon(12, 12, 24, shadow=False)}
      </g>
    """


def unhider_badge(x: float, y: float) -> str:
    """Mirrors .ru-panel__badge: orange pill, uppercase 'UNHIDER'."""
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="74" height="20" rx="10" fill="url(#brandH)"/>
        <text x="37" y="14" text-anchor="middle" font-family="{FONT}"
              font-size="10" font-weight="700" fill="#fff" letter-spacing="0.8">UNHIDER</text>
      </g>"""


def panel_header(w: float, title: str) -> str:
    """Mirrors .ru-panel__header: badge + title + 'Hide' toggle."""
    return f"""
      <rect width="{w}" height="46" rx="11" fill="{BG_PANEL_HI}"/>
      <rect y="34" width="{w}" height="12" fill="{BG_PANEL_HI}"/>
      <rect y="45" width="{w}" height="1" fill="{BORDER}"/>
      {unhider_badge(16, 13)}
      <text x="102" y="29" font-family="{FONT}" font-size="14" font-weight="600"
            fill="{TEXT_MID}">{escape(title)}</text>
      <g transform="translate({w - 72}, 11)">
        <rect width="56" height="24" rx="6" fill="none" stroke="{BORDER}"/>
        <text x="28" y="16" text-anchor="middle" font-family="{FONT}"
              font-size="12" fill="{TEXT_LOW}">Hide</text>
      </g>"""


def section_header(x: float, y: float, text: str) -> str:
    """Mirrors .ru-section-h: small uppercase bold heading."""
    return f"""
      <text x="{x}" y="{y}" font-family="{FONT}" font-size="12" font-weight="700"
            fill="{TEXT_HI}" letter-spacing="0.8">{escape(text)}</text>"""


def post_item(x: float, y: float, w: float, title: str, meta: str, body: str = "") -> str:
    """Mirrors .ru-item: soft card, bold title with meta on the same line, body below."""
    h = 62 if body else 44
    body_svg = (
        f'<text x="14" y="48" font-family="{FONT}" font-size="12.5" '
        f'fill="{TEXT_MID}">{escape(body)}</text>'
        if body else ""
    )
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="{h}" rx="8" fill="{BG_PANEL_HI}"/>
        <rect width="3" height="{h}" rx="1.5" fill="url(#brand)"/>
        <text x="14" y="26" font-family="{FONT}" font-size="14" font-weight="700"
              fill="{TEXT_HI}">{escape(title)}<tspan dx="12" font-size="11.5"
              font-weight="400" fill="{TEXT_LOW}">{escape(meta)}</tspan></text>
        {body_svg}
      </g>"""


def comment_item(x: float, y: float, w: float, thread: str, meta: str, lines: list) -> str:
    """Mirrors a comment .ru-item: muted 'Comment in r/…' link line, then body."""
    h = 40 + len(lines) * 21
    body = "".join(
        f'<text x="14" y="{46 + i * 21}" font-family="{FONT}" font-size="13" '
        f'fill="{TEXT_MID}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="{h}" rx="8" fill="{BG_PANEL_HI}"/>
        <rect width="3" height="{h}" rx="1.5" fill="url(#brand)"/>
        <text x="14" y="23" font-family="{FONT}" font-size="12" font-weight="600"
              fill="{ORANGE_LIGHT}">{escape(thread)}<tspan dx="12" font-size="11.5"
              font-weight="400" fill="{TEXT_LOW}">{escape(meta)}</tspan></text>
        {body}
        <text x="{w - 14}" y="23" text-anchor="end" font-family="{FONT}"
              font-size="11.5" font-weight="700" fill="url(#brandH)">view thread &#8599;</text>
      </g>"""


def hidden_notice(x: float, y: float, w: float, line1: str, line2: str) -> str:
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="60" rx="10" fill="{BG_PANEL}" stroke="{BORDER}"/>
        <circle cx="34" cy="30" r="15" fill="{ACCENT_HIDDEN}" fill-opacity="0.16"/>
        <text x="34" y="36" text-anchor="middle" font-family="{FONT}"
              font-size="18" font-weight="800" fill="{ACCENT_HIDDEN}">!</text>
        <text x="62" y="26" font-family="{FONT}" font-size="14" font-weight="700"
              fill="{TEXT_HI}">{escape(line1)}</text>
        <text x="62" y="46" font-family="{FONT}" font-size="13"
              fill="{TEXT_LOW}">{escape(line2)}</text>
      </g>"""


def callout_chip(x: float, y: float, w: float, label: str) -> str:
    return f"""
      <g transform="translate({x}, {y})">
        <rect x="0" y="-15" width="{w}" height="30" rx="15" fill="{ACCENT_HIDDEN}" fill-opacity="0.12"
              stroke="{ACCENT_HIDDEN}" stroke-opacity="0.45"/>
        <circle cx="14" cy="0" r="4" fill="{ACCENT_HIDDEN}"/>
        <text x="28" y="5" font-family="{FONT}" font-size="12" font-weight="800"
              fill="{ACCENT_HIDDEN}" letter-spacing="0.8">{escape(label)}</text>
      </g>"""


# ----------------------------------------------------------------------
# 1) Small promo tile — 440x280
# ----------------------------------------------------------------------
def small_promo() -> str:
    W, H = 440, 280
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>
      <g fill="#FFFFFF" fill-opacity="0.04">
        {"".join(f'<circle cx="{x}" cy="{y}" r="1.2"/>' for x in range(20, W, 28) for y in range(20, H, 28))}
      </g>
      {app_icon(110, 140, 150)}
      <text x="208" y="118" font-family="{FONT}"
            font-size="26" font-weight="800" fill="{TEXT_HI}" letter-spacing="-0.4">Reddit Profile</text>
      <text x="208" y="148" font-family="{FONT}"
            font-size="26" font-weight="800" fill="url(#brandH)" letter-spacing="-0.4">Unhider</text>
      <text x="208" y="184" font-family="{FONT}"
            font-size="13" font-weight="500" fill="{TEXT_MID}">See hidden, deleted &amp; removed</text>
      <text x="208" y="202" font-family="{FONT}"
            font-size="13" font-weight="500" fill="{TEXT_MID}">content — automatically.</text>
      <rect x="208" y="222" width="166" height="28" rx="14" fill="url(#brandH)"/>
      <text x="291" y="241" text-anchor="middle" font-family="{FONT}"
            font-size="11" font-weight="700" fill="#fff" letter-spacing="0.6">NO TRACKING · MV3</text>
    </svg>"""


# ----------------------------------------------------------------------
# 2) Marquee promo tile — 1400x560
# ----------------------------------------------------------------------
def marquee_promo() -> str:
    W, H = 1400, 560
    card_x, card_y = 860, 100
    card_w, card_h = 480, 360
    rows = [
        ("Anyone else's CRT make this sound on cold mornings?", "r/retrogaming · 312 pts"),
        ("Built a tiny CLI for managing GPG keys", "r/programming · 1.2k pts"),
        ("Sourdough starter died — autopsy thread", "r/Breadit · 88 pts"),
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>
      <g fill="#FFFFFF" fill-opacity="0.035">
        {"".join(f'<circle cx="{x}" cy="{y}" r="1.4"/>' for x in range(30, W, 36) for y in range(30, H, 36))}
      </g>

      <!-- LEFT: icon + headline -->
      {app_icon(140, 220, 200)}
      <text x="260" y="200" font-family="{FONT}"
            font-size="46" font-weight="800" fill="{TEXT_HI}" letter-spacing="-1.2">Reddit Profile</text>
      <text x="260" y="250" font-family="{FONT}"
            font-size="46" font-weight="800" fill="url(#brandH)" letter-spacing="-1.2">Unhider</text>
      <text x="260" y="298" font-family="{FONT}"
            font-size="18" font-weight="500" fill="{TEXT_MID}">See posts &amp; comments hidden on a profile —</text>
      <text x="260" y="322" font-family="{FONT}"
            font-size="18" font-weight="500" fill="{TEXT_MID}">plus deleted &amp; removed content in threads.</text>
      <text x="260" y="346" font-family="{FONT}"
            font-size="18" font-weight="500" fill="{TEXT_MID}">Pulled from the public archive, automatically.</text>

      <!-- feature chips -->
      <g font-family="{FONT}" font-size="13" font-weight="700" fill="{TEXT_HI}">
        <g>
          <rect x="260" y="400" width="140" height="36" rx="18" fill="{BG_PANEL}" stroke="{BORDER}"/>
          <text x="330" y="423" text-anchor="middle">Zero clicks</text>
        </g>
        <g>
          <rect x="412" y="400" width="168" height="36" rx="18" fill="{BG_PANEL}" stroke="{BORDER}"/>
          <text x="496" y="423" text-anchor="middle">Works in threads</text>
        </g>
        <g>
          <rect x="592" y="400" width="140" height="36" rx="18" fill="{BG_PANEL}" stroke="{BORDER}"/>
          <text x="662" y="423" text-anchor="middle">No tracking</text>
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
        <text x="{card_x + 56}" y="{card_y + 66}" text-anchor="middle" font-family="{FONT}"
              font-size="18" font-weight="800" fill="{ACCENT_HIDDEN}">!</text>
        <text x="{card_x + 84}" y="{card_y + 56}" font-family="{FONT}"
              font-size="13" font-weight="700" fill="{TEXT_HI}">u/example likes to keep their posts hidden</text>
        <text x="{card_x + 84}" y="{card_y + 76}" font-family="{FONT}"
              font-size="12" fill="{TEXT_LOW}">…but the archive remembers.</text>

        <!-- arrow -->
        <g transform="translate({card_x + card_w / 2 - 14}, {card_y + 108})">
          <circle cx="14" cy="14" r="14" fill="url(#brandH)"/>
          <path d="M 9 14 L 19 14 M 15 10 L 19 14 L 15 18" stroke="#fff" stroke-width="2"
                fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </g>

        <!-- panel header strip, real-UI style -->
        <g transform="translate({card_x + 24}, {card_y + 152})">
          {unhider_badge(0, 0)}
          <text x="86" y="15" font-family="{FONT}" font-size="13" font-weight="600"
                fill="{TEXT_MID}">Restoring hidden posts for u/example</text>
        </g>

        <!-- mock posts -->
        {"".join(marquee_row(card_x + 24, card_y + 188 + i * 50, card_w - 48, title, sub)
                 for i, (title, sub) in enumerate(rows))}
      </g>
    </svg>"""


def marquee_row(x: float, y: float, w: float, title: str, sub: str) -> str:
    return f"""
      <rect x="{x}" y="{y}" width="{w}" height="40" rx="6" fill="{BG_PANEL}"/>
      <rect x="{x}" y="{y}" width="3" height="40" rx="1.5" fill="url(#brand)"/>
      <text x="{x + 14}" y="{y + 17}" font-family="{FONT}"
            font-size="13" font-weight="700" fill="{TEXT_HI}">{escape(title)}</text>
      <text x="{x + 14}" y="{y + 32}" font-family="{FONT}"
            font-size="11" fill="{TEXT_LOW}">{escape(sub)}</text>
    """


# ----------------------------------------------------------------------
# 3) Screenshot 1 — hidden profile, restored (1280x800)
# ----------------------------------------------------------------------
def screenshot_hero() -> str:
    W, H = 1280, 800
    frame_x, frame_y = 80, 96
    frame_w, frame_h = W - 160, H - 152
    content_x = frame_x + 28
    content_y = frame_y + 44 + 24
    content_w = frame_w - 56
    panel_y = content_y + 132
    panel_w = content_w

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

      <text x="{W/2}" y="44" text-anchor="middle" font-family="{FONT}"
            font-size="24" font-weight="800" fill="{TEXT_HI}" letter-spacing="-0.4">
        Hidden profile? Restored automatically.
      </text>
      <text x="{W/2}" y="74" text-anchor="middle" font-family="{FONT}"
            font-size="14" fill="{TEXT_LOW}">
        Open the profile — the archive panel appears on its own. No clicks, no setup.
      </text>

      {browser_frame(frame_x, frame_y, frame_w, frame_h, "reddit.com/user/example/")}

      <!-- avatar + username -->
      <circle cx="{content_x + 28}" cy="{content_y + 26}" r="24" fill="url(#brand)"/>
      <text x="{content_x + 28}" y="{content_y + 33}" text-anchor="middle" font-family="{FONT}"
            font-size="21" font-weight="800" fill="#fff">e</text>
      <text x="{content_x + 64}" y="{content_y + 22}" font-family="{FONT}"
            font-size="21" font-weight="800" fill="{TEXT_HI}">u/example</text>
      <text x="{content_x + 64}" y="{content_y + 42}" font-family="{FONT}"
            font-size="12" fill="{TEXT_LOW}">3y · 12.4k karma</text>

      {hidden_notice(content_x, content_y + 64, content_w,
                     "u/example likes to keep their posts hidden,",
                     "but check out their stats to learn more about them.")}
      {callout_chip(content_x + content_w - 132, content_y + 94, 116, "DETECTED")}

      <!-- the injected panel, mirroring the real UI -->
      <g transform="translate({content_x}, {panel_y})">
        <rect width="{panel_w}" height="404" rx="11" fill="{BG_PANEL}" stroke="url(#brandH)" stroke-width="1.5"/>
        {panel_header(panel_w, "Restoring hidden posts and comments for u/example")}

        {section_header(18, 76, "POSTS (100+)")}
        {post_item(16, 88, panel_w - 32,
                   "Anyone else's CRT make a high-pitched whine on cold mornings?",
                   "r/retrogaming · 312 pts · 2y ago",
                   "It only happens for the first ten minutes after power-on, then settles…")}
        {post_item(16, 160, panel_w - 32,
                   "Built a tiny CLI for managing GPG keys across machines",
                   "r/programming · 1.2k pts · 1y ago",
                   "Subkeys live on a YubiKey; the tool shuffles the public parts around.")}
        {post_item(16, 232, panel_w - 32,
                   "Sourdough starter died after 4 years — full autopsy thread",
                   "r/Breadit · 88 pts · 8mo ago")}

        {section_header(18, 312, "COMMENTS (100+)")}
        {comment_item(16, 324, panel_w - 32,
                      "Comment in r/linux", "41 pts · 1y ago",
                      ["If you're already on GPG you might also like passage — it's age under the hood…"])}
      </g>
    </svg>"""


# ----------------------------------------------------------------------
# 4) Screenshot 2 — in-thread "Reveal archived" (1280x800)
# ----------------------------------------------------------------------
def _avatar(cx: float, cy: float, r: float, letter: str) -> str:
    return f"""
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#brand)"/>
      <text x="{cx}" y="{cy + r * 0.36}" text-anchor="middle" font-family="{FONT}"
            font-size="{r}" font-weight="800" fill="#fff">{escape(letter)}</text>"""


def _author_line(x: float, y: float, name: str, when: str) -> str:
    return f"""
      <text x="{x}" y="{y}" font-family="{FONT}"
            font-size="13" font-weight="700" fill="{TEXT_HI}">u/{escape(name)}<tspan
            font-weight="400" fill="{TEXT_LOW}">   ·   {escape(when)}</tspan></text>"""


def _removed_body(x: float, y: float) -> str:
    return f"""
      <text x="{x}" y="{y}" font-family="{FONT}"
            font-size="13" font-style="italic" fill="{TEXT_LOW}">[removed]</text>"""


def _reveal_pill(x: float, y: float) -> str:
    # Mirrors .ru-reveal: pill, transparent fill, border, accent text, ↺ prefix.
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="152" height="28" rx="14" fill="none" stroke="{BORDER}"/>
        <text x="16" y="19" font-family="{FONT}"
              font-size="14" font-weight="700" fill="{ORANGE_LIGHT}">&#8635;</text>
        <text x="34" y="19" font-family="{FONT}"
              font-size="12" font-weight="700" fill="{ORANGE_LIGHT}">Reveal archived</text>
      </g>"""


def _restored_block(x: float, y: float, w: float, meta: str, lines: list) -> str:
    # Mirrors .ru-restored: soft fill, orange left border, uppercase meta, body.
    h = 22 + 22 + len(lines) * 22 + 6
    body = "".join(
        f'<text x="16" y="{52 + i * 22}" font-family="{FONT}" '
        f'font-size="13.5" fill="{TEXT_HI}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="{h}" rx="7" fill="{BG_PANEL}" stroke="{BORDER}"/>
        <rect width="3" height="{h}" rx="1.5" fill="url(#brand)"/>
        <text x="16" y="26" font-family="{FONT}"
              font-size="11" font-weight="700" fill="{TEXT_LOW}" letter-spacing="0.6">{escape(meta)}</text>
        {body}
      </g>"""


def screenshot_thread() -> str:
    W, H = 1280, 800
    frame_x, frame_y = 80, 112
    frame_w, frame_h = W - 160, H - 200
    chrome_h = 44
    content_x = frame_x + 28
    content_y = frame_y + chrome_h + 26
    content_w = frame_w - 56

    restored_w = content_w - 40 - 210
    restored_lines = [
        "Finally someone gets the subkey workflow right. I've been juggling three",
        "machines with a pile of export-secret-subkey scripts for years — going to",
        "rip all of that out this weekend. Does it sync the trustdb across hosts too?",
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

      <text x="{W/2}" y="52" text-anchor="middle" font-family="{FONT}"
            font-size="24" font-weight="800" fill="{TEXT_HI}" letter-spacing="-0.4">
        Removed inside a thread? Restored right where it was.
      </text>
      <text x="{W/2}" y="84" text-anchor="middle" font-family="{FONT}"
            font-size="15" fill="{TEXT_LOW}">
        Spots [deleted] / [removed] posts &amp; comments and pulls the original back inline — one click.
      </text>

      {browser_frame(frame_x, frame_y, frame_w, frame_h, "reddit.com/r/programming/comments/abc123/built_a_tiny_cli_for_gpg/")}

      <g transform="translate({content_x}, {content_y})">
        <text x="0" y="8" font-family="{FONT}"
              font-size="19" font-weight="800" fill="{TEXT_HI}">Built a tiny CLI for managing GPG keys across machines</text>
        <text x="0" y="30" font-family="{FONT}"
              font-size="12.5" fill="{TEXT_LOW}">r/programming · Posted by u/example · 1y ago · 1.2k upvotes</text>
        <rect x="0" y="46" width="{content_w}" height="1" fill="{BORDER}"/>
        <text x="0" y="76" font-family="{FONT}"
              font-size="13.5" font-weight="700" fill="{TEXT_MID}">342 Comments</text>

        <!-- thread connector: parent comment B → nested reply C -->
        <path d="M 13 {208 + 36} L 13 {396 + 14} L 36 {396 + 14}"
              fill="none" stroke="{BORDER}" stroke-width="1.5"/>

        <!-- comment A: removed, shows the reveal button (the call to action) -->
        <g transform="translate(0, 104)">
          {_avatar(14, 14, 14, "t")}
          {_author_line(40, 12, "threadwalker", "2y ago")}
          {_removed_body(40, 40)}
          {_reveal_pill(40, 54)}
        </g>

        <!-- comment B: removed, already revealed → restored block (the payoff) -->
        <g transform="translate(0, 208)">
          {_avatar(14, 14, 14, "s")}
          {_author_line(40, 12, "saltymaintainer", "1y ago")}
          {_removed_body(40, 40)}
          {_restored_block(40, 54, restored_w, "u/saltymaintainer · 1y ago · restored from archive", restored_lines)}
          <g transform="translate({40 + restored_w + 22}, {54 + 50})">
            <rect x="0" y="-15" width="170" height="30" rx="15" fill="{ORANGE_LIGHT}" fill-opacity="0.12"
                  stroke="url(#brandH)" stroke-width="1.3"/>
            <circle cx="18" cy="0" r="4" fill="{ORANGE_LIGHT}"/>
            <text x="32" y="5" font-family="{FONT}"
                  font-size="11.5" font-weight="800" fill="{ORANGE_LIGHT}" letter-spacing="0.8">RESTORED INLINE</text>
          </g>
        </g>

        <!-- comment C: nested reply, removed, shows the reveal button -->
        <g transform="translate(36, 396)">
          {_avatar(12, 14, 12, "l")}
          {_author_line(34, 12, "lurkerdev", "1y ago")}
          {_removed_body(34, 38)}
          {_reveal_pill(34, 52)}
        </g>
      </g>
    </svg>"""


# ----------------------------------------------------------------------
# 5) Screenshot 3 — hidden comments panel (1280x800)
# ----------------------------------------------------------------------
def screenshot_comments() -> str:
    W, H = 1280, 800
    panel_x, panel_y = 140, 152
    panel_w = W - 280

    comments = [
        ("Comment in r/retrogaming", "84 pts · 2y ago",
         ["Honestly the whine is the flyback transformer aging — once it starts you can't un-hear it.",
          "Replacing the cap pack on the chassis helped mine but the whine never fully went away."]),
        ("Comment in r/linux", "41 pts · 1y ago",
         ["If you're already on GPG you might also like passage — it's age under the hood",
          "but uses a pass-like layout. Way faster than the GPG agent on slow boxes."]),
        ("Comment in r/Breadit", "19 pts · 8mo ago",
         ["Yeah, you basically need to keep at least two starters going if you care. I lost",
          "mine to a fridge that ran a degree too warm for a week — no symptoms until day 5."]),
        ("Comment in r/learnprogramming", "220 pts · 6mo ago",
         ["This is also why you shouldn't lean on hashCode for cross-process keying. If you need",
          "that, use a hash function with a stable spec — SHA-256, xxhash, whatever fits."]),
    ]
    cards = []
    y = 110
    for thread, meta, lines in comments:
        cards.append(comment_item(20, y, panel_w - 40, thread, meta, lines))
        y += 40 + len(lines) * 21 + 18
    panel_h = y - 18 + 20  # last card bottom + padding

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

      <text x="{W/2}" y="56" text-anchor="middle" font-family="{FONT}"
            font-size="24" font-weight="800" fill="{TEXT_HI}" letter-spacing="-0.4">
        Hidden comments too — every one links back to its thread.
      </text>
      <text x="{W/2}" y="88" text-anchor="middle" font-family="{FONT}"
            font-size="14" fill="{TEXT_LOW}">
        Pulled from the public Arctic Shift archive. No login. No tracking.
      </text>

      <g transform="translate({panel_x}, {panel_y})">
        <rect width="{panel_w}" height="{panel_h}" rx="11" fill="{BG_PANEL}"
              stroke="url(#brandH)" stroke-width="1.5"/>
        {panel_header(panel_w, "Restoring hidden comments for u/example")}
        {section_header(22, 92, "COMMENTS (100+)")}
        {"".join(cards)}
      </g>
    </svg>"""


# ----------------------------------------------------------------------
# 6) Screenshot 5 — "how it works" (1280x800)
# ----------------------------------------------------------------------
def screenshot_how() -> str:
    W, H = 1280, 800
    steps = [
        ("1", "Open a profile", "Visit any Reddit user page — that's the whole workflow."),
        ("2", "Hidden content is spotted", "The 'likes to keep their posts hidden' notice is detected the moment it appears."),
        ("3", "The archive fills the gap", "Hidden posts & comments are fetched from Arctic Shift, a public Reddit archive."),
        ("4", "Everything shows inline", "A panel appears right under the notice. Removed thread comments get a reveal button too."),
    ]
    cell_w = 280
    cell_gap = 24
    total = len(steps) * cell_w + (len(steps) - 1) * cell_gap
    start_x = (W - total) / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      {shared_defs()}
      <rect width="{W}" height="{H}" fill="url(#bgGlow)"/>

      <text x="{W/2}" y="118" text-anchor="middle" font-family="{FONT}"
            font-size="34" font-weight="800" fill="{TEXT_HI}" letter-spacing="-0.6">How it works</text>
      <text x="{W/2}" y="156" text-anchor="middle" font-family="{FONT}"
            font-size="16" fill="{TEXT_LOW}">
        Works on new and old Reddit. No account, no setup, no storage, no tracking.
      </text>

      {"".join(step_card(start_x + i * (cell_w + cell_gap), 230, cell_w, num, title, body)
               for i, (num, title, body) in enumerate(steps))}

      <!-- footer privacy strip -->
      <g transform="translate({W/2 - 430}, 610)">
        <rect width="860" height="80" rx="14" fill="{BG_SURFACE}" stroke="{BORDER}"/>
        <text x="430" y="36" text-anchor="middle" font-family="{FONT}"
              font-size="14" font-weight="800" fill="{TEXT_HI}" letter-spacing="0.4">
          RUNS ONLY ON
        </text>
        <text x="430" y="60" text-anchor="middle" font-family="{MONO}"
              font-size="12.5" fill="{TEXT_MID}">
          www.reddit.com · sh.reddit.com · old.reddit.com · arctic-shift.photon-reddit.com
        </text>
      </g>
    </svg>"""


def step_card(x: float, y: float, w: float, num: str, title: str, body: str) -> str:
    # naive wrap for title and body
    def wrap(text: str, width: int) -> list:
        words = text.split()
        lines, cur = [], ""
        for word in words:
            candidate = (cur + " " + word).strip()
            if len(candidate) > width and cur:
                lines.append(cur)
                cur = word
            else:
                cur = candidate
        if cur:
            lines.append(cur)
        return lines

    title_lines = wrap(title, 24)
    title_svg = "".join(
        f'<text x="20" y="{124 + i*24}" font-family="{FONT}" '
        f'font-size="18" font-weight="800" fill="{TEXT_HI}">{escape(line)}</text>'
        for i, line in enumerate(title_lines)
    )
    body_start = 124 + len(title_lines) * 24 + 12
    body_lines = wrap(body, 32)
    body_svg = "".join(
        f'<text x="20" y="{body_start + i*20}" font-family="{FONT}" '
        f'font-size="13" fill="{TEXT_MID}">{escape(line)}</text>'
        for i, line in enumerate(body_lines)
    )
    return f"""
      <g transform="translate({x}, {y})">
        <rect width="{w}" height="280" rx="14" fill="{BG_SURFACE}" stroke="{BORDER}"/>
        <circle cx="52" cy="52" r="28" fill="url(#brand)"/>
        <text x="52" y="63" text-anchor="middle" font-family="{FONT}"
              font-size="27" font-weight="800" fill="#fff">{escape(num)}</text>
        {title_svg}
        {body_svg}
      </g>
    """


def main() -> None:
    print("rendering store assets …")
    render(small_promo(), 440, 280, OUT / "promo-small-440x280.png")
    render(marquee_promo(), 1400, 560, OUT / "promo-marquee-1400x560.png")
    render(screenshot_hero(), 1280, 800, OUT / "screenshot-1-hero-1280x800.png")
    render(screenshot_thread(), 1280, 800, OUT / "screenshot-2-thread-1280x800.png")
    render(screenshot_comments(), 1280, 800, OUT / "screenshot-3-comments-1280x800.png")
    render(screenshot_how(), 1280, 800, OUT / "screenshot-5-howitworks-1280x800.png")
    print("done. (screenshot-4 is the popup composite: python3 composite_popup.py)")


if __name__ == "__main__":
    main()
