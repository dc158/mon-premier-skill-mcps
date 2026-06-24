# -*- coding: utf-8 -*-
"""
Webdesign & Co — Générateur de visuels Google Business Profile premium.
Dark luxury / NYC-LA agency style. Pillow + numpy.
"""
import os, time, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --------------------------------------------------------------------------- #
#  CONFIG / BRAND
# --------------------------------------------------------------------------- #
OUT   = "/mnt/user-data/outputs"
FONTS = os.path.join(OUT, "fonts")
os.makedirs(OUT, exist_ok=True)

VIOLET   = (124,  58, 237)   # #7C3AED
BG       = ( 10,   0,  24)   # #0A0018
BG_MID   = ( 26,   0,  53)   # #1A0035
WHITE    = (255, 255, 255)
VLIGHT   = (196, 181, 253)   # #C4B5FD
PINK     = (236,  72, 153)   # #EC4899
GREY     = (150, 140, 175)

# Platform brand colours
GOOGLE  = (66, 133, 244)
META    = (24, 119, 242)
TIKTOK  = (37, 244, 238)
WP      = (33, 117, 155)

MONT = os.path.join(FONTS, "Montserrat.ttf")
INTER = os.path.join(FONTS, "Inter.ttf")

_font_cache = {}
def font(size, weight=900, family="mont"):
    """Variable-font loader with weight axis + graceful fallback."""
    key = (size, weight, family)
    if key in _font_cache:
        return _font_cache[key]
    path = MONT if family == "mont" else INTER
    try:
        f = ImageFont.truetype(path, size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    except Exception:
        try:
            f = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except Exception:
            f = ImageFont.load_default()
    _font_cache[key] = f
    return f

# --------------------------------------------------------------------------- #
#  LOW-LEVEL HELPERS
# --------------------------------------------------------------------------- #
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))

def radial_gradient(w, h, stops, center=(0.5, 0.5), radius=None):
    """stops = [(pos0..1, (r,g,b)), ...]. numpy-accelerated."""
    cx, cy = center[0] * w, center[1] * h
    if radius is None:
        radius = math.hypot(max(cx, w - cx), max(cy, h - cy))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    dist = np.clip(dist, 0, 1)
    img = np.zeros((h, w, 3), np.float32)
    ps = [s[0] for s in stops]
    cs = [np.array(s[1], np.float32) for s in stops]
    for i in range(len(stops) - 1):
        m = (dist >= ps[i]) & (dist <= ps[i + 1])
        t = (dist[m] - ps[i]) / max(ps[i + 1] - ps[i], 1e-6)
        for c in range(3):
            img[..., c][m] = cs[i][c] + (cs[i + 1][c] - cs[i][c]) * t
    img[dist <= ps[0]] = cs[0]
    img[dist >= ps[-1]] = cs[-1]
    return Image.fromarray(img.astype(np.uint8), "RGB")

def linear_gradient(w, h, c0, c1, vertical=True):
    if vertical:
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        base = np.zeros((h, w, 3), np.float32)
    else:
        t = np.linspace(0, 1, w, dtype=np.float32)[None, :]
        base = np.zeros((h, w, 3), np.float32)
    for c in range(3):
        val = c0[c] + (c1[c] - c0[c]) * t
        base[..., c] = val
    return Image.fromarray(base.astype(np.uint8), "RGB")

def glow(canvas, center, radius, color, intensity=140):
    """Soft radial glow composited additively (premium look)."""
    w, h = canvas.size
    cx, cy = center
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2.2 * intensity
    layer = np.zeros((h, w, 4), np.float32)
    for c in range(3):
        layer[..., c] = color[c]
    layer[..., 3] = a
    g = Image.fromarray(layer.astype(np.uint8), "RGBA")
    canvas.alpha_composite(g)

def noise_grain(w, h, amount=10, tint=WHITE):
    """numpy random-pixel grain with very low alpha."""
    rng = np.random.default_rng(7)
    a = rng.integers(0, amount, (h, w), dtype=np.uint8)
    layer = np.zeros((h, w, 4), np.uint8)
    layer[..., 0] = tint[0]; layer[..., 1] = tint[1]; layer[..., 2] = tint[2]
    layer[..., 3] = a
    return Image.fromarray(layer, "RGBA")

def scan_lines(w, h, alpha=8, step=3):
    layer = np.zeros((h, w, 4), np.uint8)
    layer[::step, :, 3] = alpha
    return Image.fromarray(layer, "RGBA")

def dot_grid(draw, x0, y0, x1, y1, gap=26, r=1, color=(255, 255, 255, 22)):
    y = y0
    while y < y1:
        x = x0
        while x < x1:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
            x += gap
        y += gap

def bokeh(w, h, n=80, seed=3, palette=(VIOLET, PINK, VLIGHT)):
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rng = random.Random(seed)
    for _ in range(n):
        x, y = rng.randint(0, w), rng.randint(0, h)
        rad = rng.randint(6, 60)
        col = rng.choice(palette)
        a = rng.randint(8, 40)
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col + (a,))
    return layer.filter(ImageFilter.GaussianBlur(14))

def rounded(draw, box, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def glass_card(canvas, box, r=20, fill=(255, 255, 255, 16),
               border=(255, 255, 255, 40), bw=1):
    """Glassmorphism: blurred translucent panel + subtle white border."""
    w, h = canvas.size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rounded(d, box, r, fill=fill)
    rounded(d, box, r, outline=border, width=bw)
    canvas.alpha_composite(layer)

def text(draw, pos, s, fnt, fill, anchor="la", spacing=4, tracking=0):
    if tracking and len(s) > 1:
        x, y = pos
        for ch in s:
            draw.text((x, y), ch, font=fnt, fill=fill, anchor="la")
            x += draw.textlength(ch, font=fnt) + tracking
        return
    draw.text(pos, s, font=fnt, fill=fill, anchor=anchor, spacing=spacing)

def text_w(draw, s, fnt, tracking=0):
    w = draw.textlength(s, font=fnt)
    if tracking and len(s) > 1:
        w += tracking * (len(s) - 1)
    return w

def pill(canvas, x, y, label, fnt, fg=WHITE, dot=None,
         bg=(255, 255, 255, 18), border=(124, 58, 237, 160), pad=18, h=None):
    d0 = ImageDraw.Draw(canvas)
    tw = text_w(d0, label, fnt)
    extra = 26 if dot else 0
    ph = h or (fnt.size + 20)
    box = [x, y, x + tw + pad * 2 + extra, y + ph]
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rounded(d, box, ph // 2, fill=bg, outline=border, width=2)
    canvas.alpha_composite(layer)
    tx = x + pad
    if dot:
        cy = y + ph // 2
        d0.ellipse([tx, cy - 5, tx + 10, cy + 5], fill=dot)
        tx += extra
    d0.text((tx, y + ph // 2), label, font=fnt, fill=fg, anchor="lm")
    return box[2] - box[0]

def finish(canvas, grain=9, scan=True, tint=WHITE):
    w, h = canvas.size
    canvas.alpha_composite(noise_grain(w, h, grain, tint))
    if scan:
        canvas.alpha_composite(scan_lines(w, h, 6, 3))
    return canvas.convert("RGB")

def vignette(canvas, strength=120):
    w, h = canvas.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h / 2
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / math.hypot(cx, cy)
    a = np.clip(d - 0.45, 0, 1) ** 2 * strength
    layer = np.zeros((h, w, 4), np.uint8)
    layer[..., 3] = a.astype(np.uint8)
    canvas.alpha_composite(Image.fromarray(layer, "RGBA"))

# Mini browser-window mock --------------------------------------------------- #
def browser_mock(canvas, box, accent=VIOLET, title="webdesignandco.fr"):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # shadow
    rounded(d, [x0 + 10, y0 + 16, x1 + 10, y1 + 16], 16, fill=(0, 0, 0, 90))
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(12)))
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rounded(d, box, 14, fill=(18, 10, 36, 255), outline=(255, 255, 255, 40), width=1)
    bar = y0 + 34
    rounded(d, [x0, y0, x1, bar], 14, fill=(30, 18, 55, 255))
    d.rectangle([x0, bar - 14, x1, bar], fill=(30, 18, 55, 255))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([x0 + 16 + i * 20, y0 + 12, x0 + 26 + i * 20, y0 + 22], fill=col)
    rounded(d, [x0 + 90, y0 + 9, x1 - 16, y0 + 26], 8, fill=(12, 6, 24, 255))
    d.text((x0 + 102, y0 + 17), title, font=font(11, 600, "inter"),
           fill=(160, 150, 185), anchor="lm")
    canvas.alpha_composite(layer)
    # site content
    cx0, cy0, cx1, cy1 = x0 + 18, bar + 18, x1 - 18, y1 - 18
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rounded(d, [cx0, cy0, cx1, cy0 + (cy1 - cy0) * 0.42], 10, fill=accent + (190,))
    d.rectangle([cx0, cy0 + 14, cx0 + 90, cy0 + 22], fill=(255, 255, 255, 230))
    d.rectangle([cx0, cy0 + 30, cx0 + 150, cy0 + 38], fill=(255, 255, 255, 150))
    yb = cy0 + (cy1 - cy0) * 0.42 + 16
    for i in range(3):
        bx = cx0 + i * ((cx1 - cx0) / 3)
        rounded(d, [bx, yb, bx + (cx1 - cx0) / 3 - 12, cy1], 8,
                fill=(255, 255, 255, 22), outline=(255, 255, 255, 40))
    canvas.alpha_composite(layer)

# --------------------------------------------------------------------------- #
#  1. COVER
# --------------------------------------------------------------------------- #
def make_cover():
    W, H = 1080, 608
    c = radial_gradient(W, H, [(0.0, BG_MID), (0.5, (21, 0, 44)), (1.0, BG)],
                        center=(0.32, 0.5)).convert("RGBA")
    c.alpha_composite(bokeh(W, H, 70, seed=11))
    glow(c, (300, 300), 380, VIOLET, 150)
    glow(c, (250, 180), 200, PINK, 60)
    d = ImageDraw.Draw(c)
    dot_grid(d, 40, 40, W - 40, H - 40, gap=30, r=1, color=(255, 255, 255, 14))

    # badge
    pill(c, 70, 64, "AGENCE DIGITALE", font(16, 700), dot=VLIGHT,
         border=(124, 58, 237, 200))

    # headline — auto-fit so it never collides with the mock on the right
    hf = font(86, 900)
    while d.textlength("WEBDESIGN", font=hf) > 500 and hf.size > 60:
        hf = font(hf.size - 2, 900)
    d.text((70, 150), "WEBDESIGN", font=hf, fill=WHITE, anchor="la")
    d.text((70, 150 + hf.size + 14), "& CO", font=hf, fill=VIOLET, anchor="la")
    # tagline
    ty = 150 + (hf.size + 14) * 2 + 18
    d.line([74, ty - 6, 320, ty - 6], fill=VIOLET + (255,), width=3)
    text(d, (74, ty + 8), "AGENCE DIGITALE FRANCO-ÉMIRATIE",
         font(17, 700, "inter"), VLIGHT, tracking=3)

    # laptop / browser mock right
    browser_mock(c, [624, 150, 1014, 426])

    # stat cards bottom
    def stat(x, big, small):
        glass_card(c, [x, 470, x + 230, 556], r=18)
        dd = ImageDraw.Draw(c)
        dd.text((x + 20, 488), big, font=font(34, 900), fill=WHITE, anchor="lm")
        dd.text((x + 20, 528), small, font=font(13, 600, "inter"),
                fill=VLIGHT, anchor="lm")
    stat(70, "100%", "CLIENTS SATISFAITS")
    stat(320, "30 J", "LIVRAISON EXPRESS")

    vignette(c, 90)
    return finish(c)

# --------------------------------------------------------------------------- #
#  2. SERVICE WEB
# --------------------------------------------------------------------------- #
def make_service_web():
    W, H = 1200, 900
    c = radial_gradient(W, H, [(0.0, BG_MID), (0.55, (20, 0, 42)), (1.0, BG)],
                        center=(0.28, 0.35)).convert("RGBA")
    c.alpha_composite(bokeh(W, H, 60, seed=22))
    glow(c, (260, 360), 420, VIOLET, 130)
    d = ImageDraw.Draw(c)
    dot_grid(d, 40, 40, W - 40, H - 40, 34, 1, (255, 255, 255, 12))

    pill(c, 80, 90, "CRÉATION WEB", font(16, 700), dot=PINK)
    text(d, (76, 165), "CRÉATION", font(96, 900), WHITE)
    text(d, (76, 270), "DE SITES", font(96, 900), VIOLET)
    text(d, (76, 375), "WEB", font(96, 900), WHITE)
    d.text((80, 500), "Sites vitrines, e-commerce & sur-mesure",
           font=font(22, 500, "inter"), fill=VLIGHT, anchor="la")

    # tech tags
    x = 80
    for t, col in [("WordPress", WP), ("WooCommerce", VIOLET), ("Elementor", PINK)]:
        x += pill(c, x, 560, t, font(16, 700), dot=col,
                  border=col + (180,)) + 16

    # stacked devices (desktop / tablet / mobile)
    # desktop
    browser_mock(c, [690, 150, 1110, 430], accent=VIOLET)
    d.rectangle([840, 430, 960, 452], fill=(40, 26, 70, 255))
    rounded(d, [770, 452, 1030, 462], 5, fill=(50, 32, 84, 255))
    # tablet
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(layer)
    rounded(dl, [700, 510, 920, 800], 18, fill=(18, 10, 36, 255),
            outline=(255, 255, 255, 45), width=1)
    rounded(dl, [716, 540, 904, 770], 8, fill=VIOLET + (160,))
    c.alpha_composite(layer)
    # mobile
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0)); dl = ImageDraw.Draw(layer)
    rounded(dl, [955, 540, 1095, 820], 22, fill=(14, 6, 30, 255),
            outline=(255, 255, 255, 50), width=1)
    rounded(dl, [968, 565, 1082, 805], 14, fill=PINK + (150,))
    dl.rounded_rectangle([1005, 552, 1045, 560], 4, fill=(255, 255, 255, 60))
    c.alpha_composite(layer)

    # stat cards floating
    cards = [("+150%", "TRAFIC"), ("30 J", "LIVRAISON"), ("SEO", "INCLUS")]
    for i, (b, s) in enumerate(cards):
        x = 80 + i * 215
        glass_card(c, [x, 680, x + 195, 790], r=18)
        dd = ImageDraw.Draw(c)
        dd.text((x + 22, 718), b, font=font(38, 900), fill=VLIGHT, anchor="lm")
        dd.text((x + 22, 760), s, font=font(14, 600, "inter"), fill=GREY, anchor="lm")

    vignette(c, 100)
    return finish(c)

# --------------------------------------------------------------------------- #
#  3. SERVICE IA  (neural network)
# --------------------------------------------------------------------------- #
def make_service_ia():
    W, H = 1200, 900
    c = radial_gradient(W, H, [(0.0, (24, 2, 50)), (0.6, (16, 0, 38)), (1.0, BG)],
                        center=(0.6, 0.4)).convert("RGBA")
    glow(c, (820, 320), 460, VIOLET, 120)
    glow(c, (980, 220), 230, PINK, 70)

    # neural net
    rng = random.Random(42)
    nodes = [(rng.randint(560, 1140), rng.randint(80, 820)) for _ in range(26)]
    net = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(net)
    for i, p in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            q = nodes[j]
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 230:
                nd.line([p, q], fill=(124, 58, 237, 70), width=1)
    c.alpha_composite(net.filter(ImageFilter.GaussianBlur(0.6)))
    # particles + nodes glow
    for p in nodes:
        glow(c, p, 34, lerp(VIOLET, PINK, random.random()), 90)
    nd2 = ImageDraw.Draw(c)
    for p in nodes:
        nd2.ellipse([p[0]-4, p[1]-4, p[0]+4, p[1]+4], fill=WHITE+(255,))
        nd2.ellipse([p[0]-2, p[1]-2, p[0]+2, p[1]+2], fill=VLIGHT+(255,))

    d = ImageDraw.Draw(c)
    pill(c, 80, 90, "IA & AUTOMATION", font(16, 700), dot=TIKTOK,
         border=(37, 244, 238, 160))
    text(d, (76, 165), "INTELLIGENCE", font(82, 900), WHITE)
    text(d, (76, 262), "ARTIFICIELLE", font(82, 900), VIOLET)
    d.text((80, 372), "Des agents autonomes au service de votre croissance",
           font=font(21, 500, "inter"), fill=VLIGHT, anchor="la")

    # cards
    data = [("Agent CM", "Création & publication de contenu social 24/7"),
            ("Agent Marketing", "Campagnes, emailing & nurturing automatisés"),
            ("Chatbot IA", "Support client instantané multilingue")]
    for i, (t, s) in enumerate(data):
        y = 470 + i * 130
        glass_card(c, [80, y, 600, y + 110], r=20)
        dd = ImageDraw.Draw(c)
        # icon chip
        layer = Image.new("RGBA", c.size, (0, 0, 0, 0)); il = ImageDraw.Draw(layer)
        rounded(il, [102, y + 26, 160, y + 84], 16, fill=VIOLET + (220,))
        c.alpha_composite(layer)
        dd.text((131, y + 55), "★", font=font(30, 900), fill=WHITE, anchor="mm")
        dd.text((184, y + 38), t, font=font(28, 800), fill=WHITE, anchor="lm")
        dd.text((184, y + 76), s, font=font(15, 500, "inter"), fill=GREY, anchor="lm")
    vignette(c, 100)
    return finish(c)

# --------------------------------------------------------------------------- #
#  4. SERVICE ADS (dashboard)
# --------------------------------------------------------------------------- #
def make_service_ads():
    W, H = 1200, 900
    c = radial_gradient(W, H, [(0.0, BG_MID), (0.55, (20, 0, 42)), (1.0, BG)],
                        center=(0.3, 0.4)).convert("RGBA")
    c.alpha_composite(bokeh(W, H, 55, seed=33, palette=(VIOLET, PINK)))
    glow(c, (300, 400), 400, PINK, 90)
    glow(c, (240, 300), 320, VIOLET, 110)
    d = ImageDraw.Draw(c)
    dot_grid(d, 40, 40, W - 40, H - 40, 34, 1, (255, 255, 255, 10))

    pill(c, 80, 90, "CAMPAGNES ADS", font(16, 700), dot=GOOGLE)
    text(d, (76, 165), "PUBLICITÉ", font(94, 900), WHITE)
    # gradient title "DIGITALE" violet->pink
    base = "DIGITALE"
    x = 80
    fnt = font(94, 900)
    n = len(base)
    for i, ch in enumerate(base):
        col = lerp(VIOLET, PINK, i / max(n - 1, 1))
        d.text((x, 270), ch, font=fnt, fill=col, anchor="la")
        x += d.textlength(ch, font=fnt)
    d.text((80, 400), "Google, Meta & TikTok Ads pilotés par la data",
           font=font(21, 500, "inter"), fill=VLIGHT, anchor="la")

    # platform pills
    x = 80
    for t, col in [("Google Ads", GOOGLE), ("Meta Ads", META), ("TikTok Ads", TIKTOK)]:
        x += pill(c, x, 470, t, font(16, 700), dot=col, border=col + (180,)) + 16

    # stat cards
    cards = [("+300%", "LEADS", VLIGHT), ("-40%", "CPA", PINK), ("320%", "ROI", VIOLET)]
    for i, (b, s, col) in enumerate(cards):
        xx = 80 + i * 200
        glass_card(c, [xx, 560, xx + 180, 670], r=18)
        dd = ImageDraw.Draw(c)
        dd.text((xx + 20, 600), b, font=font(36, 900), fill=col, anchor="lm")
        dd.text((xx + 20, 642), s, font=font(14, 600, "inter"), fill=GREY, anchor="lm")

    # dashboard panel right
    px0, py0, px1, py1 = 700, 150, 1110, 520
    glass_card(c, [px0, py0, px1, py1], r=22, fill=(255, 255, 255, 14))
    dd = ImageDraw.Draw(c)
    dd.text((px0 + 26, py0 + 28), "PERFORMANCE", font=font(16, 800), fill=WHITE, anchor="lm")
    dd.text((px0 + 26, py0 + 52), "Live dashboard", font=font(12, 500, "inter"),
            fill=GREY, anchor="lm")
    dd.ellipse([px1 - 44, py0 + 22, px1 - 28, py0 + 38], fill=(39, 201, 63, 255))
    # rising bars
    rng = random.Random(7)
    bx0, bbase = px0 + 30, py1 - 70
    heights = [70, 95, 88, 130, 120, 165, 150, 200]
    bw = 34
    for i, hgt in enumerate(heights):
        x = bx0 + i * (bw + 12)
        col = lerp(VIOLET, PINK, i / (len(heights) - 1))
        layer = Image.new("RGBA", c.size, (0, 0, 0, 0)); bl = ImageDraw.Draw(layer)
        rounded(bl, [x, bbase - hgt, x + bw, bbase], 8, fill=col + (235,))
        c.alpha_composite(layer)
    dd = ImageDraw.Draw(c)
    dd.line([bx0 - 8, bbase + 6, px1 - 24, bbase + 6], fill=(255, 255, 255, 40), width=1)
    # rising trend curve in pink
    pts = []
    for i, hgt in enumerate(heights):
        x = bx0 + i * (bw + 12) + bw / 2
        pts.append((x, bbase - hgt - 14))
    dd.line(pts, fill=PINK + (255,), width=4, joint="curve")
    for p in pts:
        dd.ellipse([p[0]-4, p[1]-4, p[0]+4, p[1]+4], fill=WHITE+(255,))
    vignette(c, 100)
    return finish(c)

# --------------------------------------------------------------------------- #
#  5. ZONE GEO (split France / Dubai)
# --------------------------------------------------------------------------- #
def make_zone_geo():
    W, H = 1200, 900
    c = Image.new("RGBA", (W, H), BG + (255,))
    left = radial_gradient(W // 2, H, [(0.0, (22, 4, 48)), (1.0, BG)],
                           center=(0.5, 0.35)).convert("RGBA")
    right = radial_gradient(W // 2, H, [(0.0, (30, 6, 52)), (1.0, BG)],
                            center=(0.5, 0.35)).convert("RGBA")
    c.paste(left, (0, 0)); c.paste(right, (W // 2, 0))
    glow(c, (300, 320), 340, VIOLET, 90)
    glow(c, (900, 320), 340, PINK, 80)
    d = ImageDraw.Draw(c)

    # top accent borders: FR tricolore (left), UAE (right)
    tri = [(0, 0, 200, 8, (0, 85, 164)), (200, 0, 400, 8, WHITE),
           (400, 0, 600, 8, (239, 65, 53))]
    for x0, _, x1, _, col in tri:
        d.rectangle([x0, 0, x1, 8], fill=col)
    uae = [(600, 0, 750, 8, (0, 122, 61)), (750, 0, 900, 8, WHITE),
           (900, 0, 1050, 8, (0, 0, 0)), (1050, 0, 1200, 8, (206, 17, 38))]
    for x0, _, x1, _, col in uae:
        d.rectangle([x0, 0, x1, 8], fill=col)
    d.rectangle([0, 0, 50, 8], fill=(206, 17, 38))  # UAE red bar left edge of flag

    def side(ox, flag, city, accent, targets, stats):
        dd = ImageDraw.Draw(c)
        pill(c, ox + 70, 60, flag, font(15, 700), dot=accent, border=accent + (160,))
        text(dd, (ox + 66, 110), city, font(72, 900), WHITE)
        dd.line([ox + 70, 196, ox + 250, 196], fill=accent + (255,), width=3)
        dd.text((ox + 70, 220), "NOS CIBLES PRIORITAIRES",
                font=font(14, 700, "inter"), fill=accent[:3], anchor="lm")
        for i, t in enumerate(targets):
            y = 256 + i * 40
            dd.ellipse([ox + 70, y - 4, ox + 80, y + 6], outline=accent + (255,), width=2)
            dd.text((ox + 96, y + 1), t, font=font(19, 500, "inter"),
                    fill=VLIGHT, anchor="lm")
        for i, (b, s) in enumerate(stats):
            y = 470 + i * 120
            glass_card(c, [ox + 66, y, ox + 470, y + 100], r=18)
            d2 = ImageDraw.Draw(c)
            d2.text((ox + 90, y + 36), b, font=font(34, 900), fill=accent[:3], anchor="lm")
            d2.text((ox + 90, y + 74), s, font=font(14, 600, "inter"),
                    fill=GREY, anchor="lm")

    side(0, "FRANCE", "FRANCE", VIOLET,
         ["PME & startups ambitieuses", "Commerces & artisans", "Professions libérales"],
         [("60M+", "MARCHÉ FRANCOPHONE"), ("100%", "ACCOMPAGNEMENT FR")])
    side(600, "DUBAÏ — UAE", "DUBAÏ", PINK,
         ["Entreprises franco-émiraties", "Luxe & immobilier", "Tech & innovation"],
         [("0%", "TVA — ZONE FRANCHE"), ("24/7", "HUB INTERNATIONAL")])

    # center separator with luminous point
    layer = Image.new("RGBA", c.size, (0, 0, 0, 0)); ll = ImageDraw.Draw(layer)
    ll.line([W // 2, 40, W // 2, H - 40], fill=(255, 255, 255, 50), width=2)
    c.alpha_composite(layer)
    glow(c, (W // 2, H // 2), 90, WHITE, 150)
    glow(c, (W // 2, H // 2), 50, VLIGHT, 200)
    d.ellipse([W//2-8, H//2-8, W//2+8, H//2+8], fill=WHITE+(255,))

    vignette(c, 110)
    return finish(c)

# --------------------------------------------------------------------------- #
#  6. LEADS (funnel + pipeline)
# --------------------------------------------------------------------------- #
def make_leads():
    W, H = 1200, 900
    c = radial_gradient(W, H, [(0.0, BG_MID), (0.55, (20, 0, 42)), (1.0, BG)],
                        center=(0.3, 0.35)).convert("RGBA")
    c.alpha_composite(bokeh(W, H, 55, seed=44))
    glow(c, (280, 340), 400, VIOLET, 120)
    glow(c, (300, 250), 240, PINK, 60)
    d = ImageDraw.Draw(c)
    dot_grid(d, 40, 40, W - 40, H - 40, 34, 1, (255, 255, 255, 10))

    pill(c, 80, 80, "GÉNÉRATION DE LEADS", font(16, 700), dot=VLIGHT)
    text(d, (76, 150), "PROSPECTS", font(82, 900), WHITE)
    text(d, (76, 245), "QUALIFIÉS", font(82, 900), VIOLET)
    text(d, (76, 340), "EN CONTINU", font(82, 900), PINK)
    d.text((80, 452), "Un flux régulier de clients prêts à signer",
           font=font(21, 500, "inter"), fill=VLIGHT, anchor="la")

    # horizontal pipeline (4 steps)
    steps = [("CAPTER", "1"), ("QUALIFIER", "2"), ("NURTURER", "3"), ("CONVERTIR", "4")]
    x = 80
    for i, (t, num) in enumerate(steps):
        col = lerp(VIOLET, PINK, i / 3)
        glass_card(c, [x, 530, x + 230, 615], r=16)
        dd = ImageDraw.Draw(c)
        layer = Image.new("RGBA", c.size, (0, 0, 0, 0)); il = ImageDraw.Draw(layer)
        il.ellipse([x + 18, 555, x + 54, 591], fill=col + (255,))
        c.alpha_composite(layer)
        dd = ImageDraw.Draw(c)
        dd.text((x + 36, 573), num, font=font(20, 900), fill=WHITE, anchor="mm")
        dd.text((x + 70, 573), t, font=font(17, 800), fill=WHITE, anchor="lm")
        if i < 3:
            dd.text((x + 240, 573), "→", font=font(26, 900), fill=col, anchor="mm")
        x += 250

    # tool pills
    x = 80
    tools = [("Waalaxy", VIOLET), ("LinkedIn", META), ("Make.com", PINK),
             ("Google Ads", GOOGLE), ("SEO", (39, 201, 63))]
    for t, col in tools:
        nx = pill(c, x, 670, t, font(15, 700), dot=col, border=col + (170,))
        x += nx + 14

    # FUNNEL right — 5 stages
    stages = [("VISITEURS", "100%", VIOLET),
              ("LEADS", "42%", lerp(VIOLET, PINK, .25)),
              ("MQL", "24%", lerp(VIOLET, PINK, .5)),
              ("SQL", "12%", lerp(VIOLET, PINK, .75)),
              ("CLIENTS", "6%", PINK)]
    cx = 930
    top_w, bot_w = 230, 70
    y = 150
    sh = 116
    for i, (label, pct, col) in enumerate(stages):
        t0 = i / len(stages); t1 = (i + 1) / len(stages)
        w0 = top_w + (bot_w - top_w) * t0
        w1 = top_w + (bot_w - top_w) * t1
        poly = [(cx - w0 / 2, y), (cx + w0 / 2, y),
                (cx + w1 / 2, y + sh - 10), (cx - w1 / 2, y + sh - 10)]
        layer = Image.new("RGBA", c.size, (0, 0, 0, 0)); fl = ImageDraw.Draw(layer)
        fl.polygon(poly, fill=col + (220,))
        c.alpha_composite(layer)
        dd = ImageDraw.Draw(c)
        dd.text((cx, y + sh / 2 - 12), label, font=font(20, 800), fill=WHITE, anchor="mm")
        dd.text((cx, y + sh / 2 + 14), pct, font=font(16, 700, "inter"),
                fill=(255, 255, 255, 220), anchor="mm")
        y += sh
    d.text((cx, 132), "TUNNEL DE CONVERSION", font=font(14, 700, "inter"),
           fill=VLIGHT, anchor="mm")
    vignette(c, 100)
    return finish(c)

# --------------------------------------------------------------------------- #
#  RUN
# --------------------------------------------------------------------------- #
JOBS = [
    ("cover.png",        make_cover),
    ("service_web.png",  make_service_web),
    ("service_ia.png",   make_service_ia),
    ("service_ads.png",  make_service_ads),
    ("zone_geo.png",     make_zone_geo),
    ("leads.png",        make_leads),
]

def main():
    print("=" * 56)
    print(" WEBDESIGN & CO — génération des visuels GBP")
    print("=" * 56)
    total = 0.0
    results = []
    for name, fn in JOBS:
        t0 = time.time()
        img = fn()
        path = os.path.join(OUT, name)
        img.save(path, "PNG", optimize=True)
        dt = time.time() - t0
        total += dt
        results.append((name, img.size, dt))
        print(f"  ✓ {name:<18} {img.size[0]}x{img.size[1]:<5}  {dt:5.2f}s")
    print("-" * 56)
    print(f"  TOTAL : {total:.2f}s pour {len(JOBS)} visuels")
    print("=" * 56)

    # index.html preview
    cards = "\n".join(
        f'''      <figure>
        <img src="{n}" alt="{n}">
        <figcaption>{n} &middot; {w}×{h}px &middot; {d:.2f}s</figcaption>
      </figure>''' for n, (w, h), d in results)
    html = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Webdesign &amp; Co — Visuels GBP</title>
<style>
  :root{{--v:#7C3AED;--p:#EC4899;--vl:#C4B5FD}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:#0A0018;color:#fff;
    font-family:'Segoe UI',system-ui,sans-serif}}
  header{{padding:48px 32px 24px;text-align:center}}
  h1{{font-size:38px;font-weight:900;letter-spacing:-1px;margin:0}}
  h1 span{{color:var(--v)}}
  p.sub{{color:var(--vl);letter-spacing:3px;font-size:13px;
    text-transform:uppercase;margin-top:10px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));
    gap:28px;padding:32px;max-width:1400px;margin:0 auto}}
  figure{{margin:0;background:rgba(255,255,255,.04);
    border:1px solid rgba(124,58,237,.35);border-radius:18px;
    overflow:hidden;transition:transform .25s,box-shadow .25s}}
  figure:hover{{transform:translateY(-6px);
    box-shadow:0 18px 50px rgba(124,58,237,.35)}}
  img{{width:100%;display:block}}
  figcaption{{padding:14px 18px;font-size:13px;color:var(--vl);
    letter-spacing:1px}}
  footer{{text-align:center;color:#6b6480;padding:30px;font-size:12px}}
</style></head><body>
  <header>
    <h1>WEBDESIGN <span>&amp; CO</span></h1>
    <p class="sub">Agence digitale franco-émiratie — Visuels Google Business Profile</p>
  </header>
  <section class="grid">
{cards}
  </section>
  <footer>Généré avec Pillow + numpy · Total {total:.2f}s</footer>
</body></html>"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("  ✓ index.html (preview)")

if __name__ == "__main__":
    main()
