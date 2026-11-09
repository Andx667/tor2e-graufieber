#!/usr/bin/env python3
"""Malt das Titelbild von „Graufieber“: trübe Marsch, Schilf, Brandhafen in der Ferne,
ein gestrandeter Kornkahn mit versiegelten Säcken, vier Gestalten in Kapuzen auf einem
Bohlenweg. Rein prozedural (numpy, OpenCV), anschließend malerisch nachbearbeitet.

    python3 tools/cover.py            # -> assets/cover-de.jpg
"""
import os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "cover-de.jpg")
W, H = 2400, 1600
HZ = int(H * 0.555)                      # Horizont
VP = (int(W * 0.615), HZ + 22)           # Fluchtpunkt des Bohlenwegs (zum Dorf hin)
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def C(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def noise(scale, octaves=5, seed=0, w=W, h=H, pers=0.5, stretch=1.0):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        cw = max(2, int(w / scale * 2 ** o / stretch)); ch = max(2, int(h / scale * 2 ** o))
        out += amp * cv2.resize(r.random((ch, cw)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp; amp *= pers
    out /= tot
    return np.clip((out - out.min()) / (out.max() - out.min() + 1e-6), 0, 1)


def lerp(a, b, t):
    return a + (b - a) * t


def blend(img, col, mask):
    return img * (1 - mask[..., None]) + col * mask[..., None]


def poly_mask(polys, ss=2):
    """Antialiasierte Füllmaske, in doppelter Auflösung gezeichnet."""
    m = np.zeros((H * ss, W * ss), np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.round(np.array(p) * ss).astype(np.int32)], 255, cv2.LINE_AA)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


img = np.zeros((H, W, 3), np.float32)
dist = np.clip((yy - HZ) / (H - HZ), 0, 1)

# ======================= Himmel =======================
t = np.clip(yy / HZ, 0, 1)
sky = lerp(C("#3b4440"), C("#717770"), np.clip(t / 0.6, 0, 1)[..., None])
sky = lerp(sky, C("#aaa58b"), np.clip((t - 0.6) / 0.4, 0, 1)[..., None] ** 1.3)
c1 = noise(520, 6, 1, stretch=2.6); c2 = noise(220, 6, 2, stretch=3.2)
clouds = np.clip((0.65 * c1 + 0.35 * c2 - 0.40) * 2.8, 0, 1)
# beleuchtete Wolkenunterseiten: dort, wo die Dichte nach unten abnimmt
under = np.clip((np.roll(clouds, -14, axis=0) - clouds) * -4, 0, 1)
sky = blend(sky, C("#20272500"[:7]), clouds * (1 - t) ** 0.6 * 0.80)
sky = blend(sky, C("#9c9880"), cv2.GaussianBlur(under, (0, 0), 4) * 0.35 * np.clip(t * 1.6, 0, 1))
# hellere Wolkensäume
rim = np.clip((0.65 * c1 + 0.35 * c2 - 0.36) * 6, 0, 1) * (1 - clouds)
sky = blend(sky, C("#8f8f7c"), rim * 0.45 * (1 - t) ** 0.5)
# fahles Licht hinter dem Dunst, links über dem Horizont
gx, gy = W * 0.30, HZ * 0.90
gl = np.exp(-(((xx - gx) / (W * 0.20)) ** 2 + ((yy - gy) / (H * 0.12)) ** 2))
sky = blend(sky, C("#e3d8ac"), np.clip(gl * 0.85, 0, 1))
gl2 = np.exp(-(((xx - gx) / (W * 0.45)) ** 2 + ((yy - gy) / (H * 0.30)) ** 2))
sky = blend(sky, C("#a39e82"), np.clip(gl2 * 0.35, 0, 1))
# Lichtbahnen durch die Wolken
for a, wdt in ((-0.32, 0.020), (-0.18, 0.012), (-0.05, 0.016)):
    d = np.abs((xx - gx) - (yy - gy) * a) / (W * wdt + (gy - yy).clip(0) * 0.05)
    beam = np.exp(-d ** 2) * (yy < gy) * np.clip((yy - gy * 0.25) / (gy * 0.75), 0, 1)
    sky = blend(sky, C("#cfc7a0"), beam * 0.10)
img[:HZ] = sky[:HZ]

# Vögel
for k in range(11):
    bx, by = W * (0.50 + rng.random() * 0.30), H * (0.10 + rng.random() * 0.20)
    s = 6 + rng.random() * 10
    pts = np.array([[bx - s, by - s * 0.15], [bx - s * 0.45, by - s * 0.5], [bx, by], [bx + s * 0.45, by - s * 0.5], [bx + s, by - s * 0.1]], np.int32)
    cv2.polylines(img, [pts], False, C("#1f2422").tolist(), 2, cv2.LINE_AA)

# ======================= Ferne Hügel =======================
hl = HZ - 10 - 46 * noise(600, 4, 3, w=W, h=1)[0] - 12 * noise(90, 3, 4, w=W, h=1)[0]
hl += 18 * np.exp(-((np.arange(W) - W * 0.12) / (W * 0.10)) ** 2)
hm = ((yy > hl[None, :]) & (yy <= HZ)).astype(np.float32)
img = blend(img, C("#757869"), hm * 0.8)
hl2 = HZ - 4 - 18 * noise(300, 4, 5, w=W, h=1)[0]
hm2 = ((yy > hl2[None, :]) & (yy <= HZ)).astype(np.float32)
img = blend(img, C("#666a5e"), hm2 * 0.8)

# ======================= Brandhafen =======================
base = HZ + 6
r2 = np.random.default_rng(11)
houses, wins = [], []
x = W * 0.585
while x < W * 0.775:
    w_ = r2.uniform(34, 70); h_ = r2.uniform(26, 46); roof = r2.uniform(16, 30)
    yb = base + r2.uniform(-4, 3) - 10 * np.exp(-((x - W * 0.67) / 120) ** 2)
    houses.append([(x, yb), (x, yb - h_), (x + w_ / 2, yb - h_ - roof), (x + w_, yb - h_), (x + w_, yb)])
    if r2.random() < 0.6:
        wins.append((x + r2.uniform(8, w_ - 10), yb - r2.uniform(8, h_ - 6)))
    x += w_ + r2.uniform(-10, 8)
tx = W * 0.785
tower = [(tx, base + 6), (tx + 5, base - 132), (tx + 22, base - 144), (tx + 30, base - 128), (tx + 46, base - 136), (tx + 50, base + 6)]
mole = [(tx - 90, base), (tx + 210, base - 2), (tx + 210, base + 8), (tx - 90, base + 10)]
ships = []
for cx_, mh in ((W * 0.845, 150), (W * 0.878, 122)):
    ships.append([(cx_ - 52, base - 10), (cx_ + 56, base - 10), (cx_ + 42, base + 8), (cx_ - 40, base + 8)])
vil = poly_mask(houses + [tower, mole] + ships)
masts = np.zeros((H, W), np.float32)
for cx_, mh in ((W * 0.845, 150), (W * 0.878, 122)):
    cv2.line(masts, (int(cx_), int(base - 10)), (int(cx_), int(base - 10 - mh)), 1.0, 3, cv2.LINE_AA)
    cv2.line(masts, (int(cx_ - 34), int(base - mh + 18)), (int(cx_ + 34), int(base - mh + 18)), 1.0, 2, cv2.LINE_AA)
    cv2.line(masts, (int(cx_), int(base - 10 - mh)), (int(cx_ + 60), int(base - 12)), 0.6, 1, cv2.LINE_AA)
vil = np.maximum(vil, masts)
img = blend(img, C("#3f4440"), vil * 0.93)
# Dächer im Dunstlicht etwas heller an der linken Kante
vedge = np.clip(vil - np.roll(vil, 3, axis=1), 0, 1)
img = blend(img, C("#8a8875"), vedge * 0.35)
# Rauch
sn = noise(70, 4, 12)
smoke = np.zeros((H, W), np.float32)
for sx in (W * 0.61, W * 0.66, W * 0.72):
    up = (base - 30 - yy).clip(0)
    col = np.exp(-((xx - sx - up * 0.55 - 40 * sn) / (6 + up * 0.10)) ** 2) * (up > 0) * (up < 520) * (1 - up / 520)
    smoke = np.maximum(smoke, col * (0.4 + 0.6 * sn))
img = blend(img, C("#8e8d7e"), np.clip(smoke * 0.55, 0, 1))
# Fenster
glow = np.zeros((H, W), np.float32)
for wx, wy in wins:
    cv2.rectangle(img, (int(wx), int(wy)), (int(wx + 4), int(wy + 6)), C("#f3b860").tolist(), -1)
    cv2.circle(glow, (int(wx + 2), int(wy + 3)), 6, 1.0, -1)
img = blend(img, C("#e7a04e"), np.clip(cv2.GaussianBlur(glow, (0, 0), 14) * 2.6, 0, 1))
village_layer = img.copy()

# ======================= Wasser =======================
refl = cv2.resize(img[:HZ][::-1], (W, H - HZ))
refl = cv2.GaussianBlur(refl, (0, 0), sigmaX=1.5, sigmaY=14)
water = refl * 0.70 + C("#283030") * 0.30
rip = cv2.resize(noise(20, 3, 21, w=W // 2, h=(H - HZ) // 10), (W, H - HZ))
water *= (0.88 + 0.24 * rip[..., None])
img[HZ:] = water
# helle Lichtbahn im Wasser unter dem Dunstlicht
lb = np.exp(-((xx - gx) / (W * 0.06 + (yy - HZ).clip(0) * 0.25)) ** 2) * (yy > HZ) * np.exp(-((yy - HZ) / (H * 0.25)))
lbn = cv2.resize(noise(12, 2, 23, w=W // 3, h=H // 30), (W, H))
img = blend(img, C("#d5ccA3".lower()), np.clip(lb * (0.3 + 0.7 * lbn) * 0.55, 0, 1))
# Watt und Schlick
mud = noise(460, 6, 22)
mudmask = np.clip((mud - 0.52 + dist * 0.22) * 6, 0, 1) * (yy > HZ + 8)
img = blend(img, lerp(C("#646050"), C("#34342c"), dist[..., None]), mudmask * 0.93)
# Schlick-Glanz an Rändern
mud_edge = np.clip(np.abs(cv2.Laplacian(mudmask, cv2.CV_32F, ksize=5)) * 0.6, 0, 1)
img = blend(img, C("#a39c80"), mud_edge * 0.25)
for k in range(320):
    ly = int(HZ + (H - HZ) * rng.random() ** 1.7)
    lx = int(W * rng.random()); ll = int(14 + 150 * (ly - HZ) / (H - HZ) * rng.random() + 8)
    if mudmask[min(ly, H - 1), min(lx, W - 1)] < 0.3:
        c = C("#b2ad91") if rng.random() < 0.55 else C("#1c2321")
        cv2.line(img, (lx, ly), (lx + ll, ly), c.tolist(), 1, cv2.LINE_AA)

# ======================= Schilf (Hilfsfunktion) =======================
def reeds(target, n, xr, yr, hr, thick, cols, seed, lean=(-0.2, 0.15), heads=0.35, tips=None):
    r = np.random.default_rng(seed)
    for _ in range(n):
        x0 = r.uniform(*xr); y0 = r.uniform(*yr); h_ = r.uniform(*hr); bend = r.uniform(*lean)
        c = lerp(C(cols[0]), C(cols[1]), r.random())
        pts = [(x0 + bend * h_ * s ** 1.8, y0 - h_ * s) for s in np.linspace(0, 1, 10)]
        tk = max(1, int(round(r.uniform(*thick))))
        cv2.polylines(target, [np.array(pts, np.int32)], False, c.tolist(), tk, cv2.LINE_AA)
        if tips is not None:   # Spitzen im Dunstlicht
            cv2.polylines(target, [np.array(pts[6:], np.int32)], False, lerp(c, C(tips), 0.5).tolist(), max(1, tk - 1), cv2.LINE_AA)
        if r.random() < heads:
            hx, hy = pts[-3]
            cv2.ellipse(target, (int(hx), int(hy)), (max(2, tk + 1), int(5 + tk * 3.2)), float(np.degrees(np.arctan(bend))), 0, 360, (c * 0.62).tolist(), -1, cv2.LINE_AA)
        if r.random() < 0.6:
            k = r.integers(2, 6); bx, by = pts[k]
            side = r.choice([-1, 1])
            leaf = [(bx, by), (bx + side * h_ * 0.10, by - h_ * 0.10), (bx + side * h_ * 0.22, by - h_ * 0.08)]
            cv2.polylines(target, [np.array(leaf, np.int32)], False, c.tolist(), max(1, tk - 1), cv2.LINE_AA)


reeds(img, 1300, (0, W), (HZ + 4, HZ + 50), (8, 26), (1, 1.6), ("#5c5e50", "#7c7a62"), 40, heads=0.03)
reeds(img, 900, (0, W * 0.40), (HZ + 40, H * 0.74), (30, 110), (1, 2.4), ("#45463a", "#867a54"), 41, heads=0.08, tips="#c9b98a")
reeds(img, 900, (W * 0.70, W), (HZ + 40, H * 0.76), (30, 110), (1, 2.4), ("#45463a", "#867a54"), 42, heads=0.08, tips="#c9b98a")

# ======================= Bohlenweg =======================
def walk_x(y, side):
    f = np.clip((y - VP[1]) / (H + 60 - VP[1]), 0, 1)
    return lerp(VP[0] + side * 10, (W * 0.215 if side < 0 else W * 0.395), f), f


bw = poly_mask([[(W * 0.215, H + 60), (W * 0.395, H + 60), (VP[0] + 10, VP[1]), (VP[0] - 10, VP[1])]])
img = blend(img, C("#1a1814"), bw * 0.95)   # Grund zwischen den Planken
r3 = np.random.default_rng(31)
n = 90
for k in range(n):
    f0 = (k / n) ** 2.15; f1 = ((k + 0.82) / n) ** 2.15
    y0 = VP[1] + (H + 60 - VP[1]) * f0; y1 = VP[1] + (H + 60 - VP[1]) * f1
    if r3.random() < 0.06 and k > 20:
        continue                               # fehlende Planke
    jit = r3.uniform(-0.03, 0.03)
    xl0, _ = walk_x(y0, -1); xr0, _ = walk_x(y0, 1); xl1, _ = walk_x(y1, -1); xr1, _ = walk_x(y1, 1)
    sh = (xr1 - xl1) * jit
    plank = [(xl0 + sh, y0), (xr0 + sh, y0), (xr1, y1), (xl1, y1)]
    tone = lerp(C("#2d2820"), C("#6a5d48"), r3.uniform(0.15, 0.75)) * (0.75 + 0.35 * f0)
    m = poly_mask([plank])
    img = blend(img, tone, m)
wg = noise(18, 3, 32, stretch=0.15)            # Maserung längs der Planken
img = blend(img, C("#15130f"), bw * np.clip((wg - 0.6) * 2, 0, 1) * 0.5)
# nasser Glanz auf dem Holz
wet = np.exp(-((xx - lerp(VP[0], W * 0.30, dist)) / (W * 0.04 + 0.1 * (yy - VP[1]).clip(0))) ** 2)
img = blend(img, C("#a8a184"), bw * wet * 0.18 * (yy > VP[1]))
# Pfähle, schief
for k in range(3, 30):
    f = (k / 30) ** 2.15
    y = VP[1] + (H + 60 - VP[1]) * f
    for side in (-1, 1):
        xp, _ = walk_x(y, side)
        ph = 8 + 95 * f; pw = max(2, 12 * f); tilt = r3.uniform(-0.08, 0.08) * ph
        post = [(xp - pw / 2, y + 6 * f), (xp + pw / 2, y + 6 * f), (xp + pw / 2 + tilt, y - ph), (xp - pw / 2 + tilt, y - ph)]
        img = blend(img, C("#16140f"), poly_mask([post]))

# ======================= Vier Gestalten =======================
def figure(cx, feet, s, gear, step, seed):
    """Kapuzengestalt von hinten, im Gehen. s = Höhe in Pixeln."""
    r = np.random.default_rng(seed)
    P = lambda dx, dy: (cx + dx * s, feet - dy * s)
    hood = [P(-0.085, 0.80), P(-0.095, 0.88), P(-0.06, 0.955), P(0.0, 0.985), P(0.035, 0.995), P(0.055, 0.96), P(0.09, 0.89), P(0.085, 0.80)]
    cloak = [P(-0.10, 0.82), P(-0.15, 0.74), P(-0.165, 0.55), P(-0.18, 0.30), P(-0.20, 0.10), P(-0.17 - 0.02 * step, 0.035),
             P(-0.06, 0.06), P(0.02, 0.03), P(0.10, 0.07), P(0.18 + 0.02 * step, 0.02), P(0.19, 0.12), P(0.175, 0.32), P(0.16, 0.56), P(0.145, 0.75), P(0.10, 0.82)]
    legs = [[P(-0.07 - 0.03 * step, 0.07), P(-0.035, 0.07), P(-0.045 - 0.04 * step, 0.0), P(-0.085 - 0.05 * step, 0.0)],
            [P(0.035, 0.06), P(0.075, 0.06), P(0.075 + 0.04 * step, 0.0), P(0.035 + 0.05 * step, 0.0)]]
    parts = [hood, cloak] + legs
    if "pack" in gear:
        parts.append([P(-0.11, 0.70), P(0.11, 0.70), P(0.12, 0.50), P(-0.12, 0.50)])
    m = poly_mask(parts)
    lines = np.zeros((H * 2, W * 2), np.uint8)
    if "spear" in gear:
        a, b = P(0.20, -0.02), P(0.24, 1.32)
        cv2.line(lines, (int(a[0] * 2), int(a[1] * 2)), (int(b[0] * 2), int(b[1] * 2)), 255, max(2, int(s * 0.045)), cv2.LINE_AA)
        tip = [P(0.236, 1.30), P(0.252, 1.42), P(0.226, 1.30)]
        cv2.fillPoly(lines, [np.round(np.array(tip) * 2).astype(np.int32)], 255, cv2.LINE_AA)
    if "staff" in gear:
        a, b = P(-0.21, -0.01), P(-0.25, 1.12)
        cv2.line(lines, (int(a[0] * 2), int(a[1] * 2)), (int(b[0] * 2), int(b[1] * 2)), 255, max(2, int(s * 0.05)), cv2.LINE_AA)
    if "bow" in gear:
        c0 = P(0.0, 0.60)
        cv2.ellipse(lines, (int(c0[0] * 2), int(c0[1] * 2)), (int(s * 0.10), int(s * 0.36)), 28, 200, 340, 255, max(2, int(s * 0.035)), cv2.LINE_AA)
    if "sword" in gear:
        a, b = P(-0.12, 0.30), P(-0.25, 0.06)
        cv2.line(lines, (int(a[0] * 2), int(a[1] * 2)), (int(b[0] * 2), int(b[1] * 2)), 255, max(2, int(s * 0.04)), cv2.LINE_AA)
    m = np.maximum(m, cv2.resize(lines, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255)
    return m


def on_walk(f):
    """Position auf dem Bohlenweg; f = 0 am Fluchtpunkt, 1 am unteren Rand."""
    y = VP[1] + (H + 60 - VP[1]) * f
    xl, _ = walk_x(y, -1); xr, _ = walk_x(y, 1)
    return (xl + xr) / 2, y, (xr - xl)


figs = np.zeros((H, W), np.float32)
specs = [(0.64, 1.02, ("spear",), 0.6, -0.06), (0.48, 1.00, ("pack", "staff"), -0.5, 0.10),
         (0.365, 0.97, ("bow",), 0.4, -0.05), (0.275, 0.95, ("sword",), -0.3, 0.07)]
for i, (f, hs, gear, step, off) in enumerate(specs):
    cx, y, wdt = on_walk(f)
    s = wdt * hs
    figs = np.maximum(figs, figure(cx + off * wdt * 0.3, y, s, gear, step, 70 + i))
# Kontaktschatten auf dem nassen Holz
img = blend(img, C("#0d0d0b"), cv2.GaussianBlur(np.clip(figs - np.roll(figs, -10, axis=0), 0, 1) * (yy > HZ), (0, 0), 6) * 0.5)
# Tuch: fast schwarz, links vom Dunstlicht gestreift, senkrechte Falten
folds = cv2.resize(noise(6, 2, 77, w=W // 4, h=8), (W, H), interpolation=cv2.INTER_CUBIC)
side = np.clip(figs - np.roll(figs, 16, axis=1), 0, 1)
side = cv2.GaussianBlur(side, (0, 0), 5)
fig_col = lerp(C("#0b0c0b"), C("#22231f"), np.clip(folds * 0.8 + side * 0.9, 0, 1)[..., None])
edge = cv2.GaussianBlur(np.clip(figs - np.roll(figs, 2, axis=1), 0, 1), (0, 0), 0.8)
fig_col = blend(fig_col, C("#8f8a70"), edge * 0.55)
img = blend(img, fig_col, figs)
figs_soft = cv2.GaussianBlur(figs, (0, 0), 0.7)

# ======================= Gestrandeter Kornkahn =======================
def bez(p0, p1, p2, n=24):
    t_ = np.linspace(0, 1, n)[:, None]
    return list(map(tuple, (1 - t_) ** 2 * np.array(p0) + 2 * (1 - t_) * t_ * np.array(p1) + t_ ** 2 * np.array(p2)))


pre_boat = img.copy()
# Rückwand und Boden des Kahns (innen, im Schatten)
back = bez((W * 0.640, H * 0.835), (W * 0.78, H * 0.865), (W * 0.955, H * 0.842)) + bez((W * 0.955, H * 0.842), (W * 0.80, H * 0.93), (W * 0.645, H * 0.905))
img = blend(img, C("#1c1914"), poly_mask([back]))
cv2.polylines(img, [np.array(bez((W * 0.640, H * 0.835), (W * 0.78, H * 0.865), (W * 0.955, H * 0.842)), np.int32)], False, C("#5d5240").tolist(), 4, cv2.LINE_AA)
# Ruderstange, schräg im Schlick
cv2.line(img, (int(W * 0.95), int(H * 0.90)), (int(W * 0.99), int(H * 0.68)), C("#1a1712").tolist(), 7, cv2.LINE_AA)


def front_hull():
    global img
    top = bez((W * 0.632, H * 0.858), (W * 0.77, H * 0.945), (W * 0.962, H * 0.900))
    bot = bez((W * 0.962, H * 0.900), (W * 0.93, H * 0.985), (W * 0.80, H * 0.990)) + bez((W * 0.80, H * 0.990), (W * 0.67, H * 0.985), (W * 0.632, H * 0.858))
    m = poly_mask([top + bot])
    sh = np.clip((yy - H * 0.90) / (H * 0.09), 0, 1)
    wood = lerp(C("#4a3f30"), C("#16130e"), sh[..., None]) * (0.85 + 0.25 * noise(30, 3, 99, stretch=6)[..., None])
    img = blend(img, wood, m)
    for k in range(1, 5):   # Klinkerplanken
        line = bez((W * 0.634, H * (0.858 + 0.012 * k)), (W * 0.77, H * (0.945 + 0.011 * k)), (W * 0.960, H * (0.900 + 0.016 * k)))
        cv2.polylines(img, [np.array(line, np.int32)], False, C("#120f0b").tolist(), 3, cv2.LINE_AA)
        cv2.polylines(img, [np.array(line, np.int32) + [0, 3]], False, C("#5a4d3a").tolist(), 1, cv2.LINE_AA)
    cv2.polylines(img, [np.array(top, np.int32)], False, C("#8a7a5c").tolist(), 5, cv2.LINE_AA)
    # Wasserlinie mit Glanz
    wl = bez((W * 0.64, H * 0.968), (W * 0.80, H * 0.985), (W * 0.95, H * 0.955))
    cv2.polylines(img, [np.array(wl, np.int32)], False, C("#8c8870").tolist(), 2, cv2.LINE_AA)


def sack(cx, cy, w_, h_, ang, seed, seal=False, upright=False):
    """Jutesack: liegend kissenförmig (Superellipse, unten gesackt), stehend mit gebundenem Hals."""
    global img
    r = np.random.default_rng(seed)
    ca, sa = np.cos(np.radians(ang)), np.sin(np.radians(ang))
    def R(dx, dy):
        return (cx + dx * ca - dy * sa, cy + dx * sa + dy * ca)
    body = []
    for th in np.linspace(0, 2 * np.pi, 64, endpoint=False):
        c, s_ = np.cos(th), np.sin(th)
        n = 3.2
        px = np.sign(c) * abs(c) ** (2 / n) * w_ / 2
        py = np.sign(s_) * abs(s_) ** (2 / n) * h_ / 2
        if s_ > 0:      # Bauch sackt nach unten und quillt seitlich
            px *= 1 + 0.06 * s_
            py *= 1 + 0.05 * (1 - abs(c))
        else:           # oben eingefallen
            py *= 1 - 0.18 * (1 - abs(c)) ** 2
        px += r.normal(0, w_ * 0.006); py += r.normal(0, h_ * 0.006)
        body.append(R(px, py))
    parts = [body]
    if upright:
        parts.append([R(-w_ * 0.16, -h_ * 0.40), R(-w_ * 0.08, -h_ * 0.58), R(-w_ * 0.16, -h_ * 0.74), R(0, -h_ * 0.66),
                      R(w_ * 0.17, -h_ * 0.76), R(w_ * 0.09, -h_ * 0.57), R(w_ * 0.16, -h_ * 0.40)])
    else:   # Zipfel an den Ecken
        for sx_ in (-1, 1):
            parts.append([R(sx_ * w_ * 0.44, -h_ * 0.30), R(sx_ * w_ * 0.56, -h_ * 0.42), R(sx_ * w_ * 0.50, -h_ * 0.20)])
    m = poly_mask(parts)
    lx = (xx - cx) * ca + (yy - cy) * sa; ly = -(xx - cx) * sa + (yy - cy) * ca
    sh = np.clip(1.0 - np.sqrt(((lx + w_ * 0.22) / (w_ * 0.80)) ** 2 + ((ly + h_ * 0.30) / (h_ * 0.95)) ** 2), 0, 1)
    burlap = lerp(C("#262118"), C("#9a8a66"), sh[..., None] ** 0.9)
    fold = noise(10, 2, seed, stretch=2.5)
    burlap *= (0.85 + 0.25 * fold[..., None])
    burlap *= (0.95 + 0.07 * (0.5 + 0.5 * np.sin(lx * 2.2) * np.sin(ly * 2.2)))[..., None]
    # Kontur dunkel, damit sich die Säcke voneinander lösen
    edge = np.clip(m - cv2.erode(m, np.ones((5, 5), np.uint8)), 0, 1)
    img = blend(img, burlap, m)
    img = blend(img, C("#17140f"), edge * 0.7)
    if not upright:   # Naht über die Länge
        pts = [R(dx, -h_ * 0.08 + 0.03 * h_ * np.sin(dx / w_ * 6)) for dx in np.linspace(-w_ * 0.40, w_ * 0.40, 12)]
        cv2.polylines(img, [np.array(pts, np.int32)], False, C("#3a3224").tolist(), 2, cv2.LINE_AA)
    else:
        q0, q1 = R(-w_ * 0.12, -h_ * 0.52), R(w_ * 0.12, -h_ * 0.52)
        cv2.line(img, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), C("#1d1810").tolist(), 4, cv2.LINE_AA)
    if seal:   # kleines, fahles Wachssiegel
        sx, sy = R(w_ * 0.18, h_ * 0.06) if not upright else R(0, -h_ * 0.47)
        sx, sy = int(sx), int(sy)
        cv2.circle(img, (sx, sy), 9, C("#b9b4a2").tolist(), -1, cv2.LINE_AA)
        cv2.circle(img, (sx - 2, sy - 2), 4, C("#d6d1bf").tolist(), -1, cv2.LINE_AA)
        cv2.line(img, (sx - 4, sy + 3), (sx + 4, sy + 3), C("#6e6a5d").tolist(), 1, cv2.LINE_AA)


# Stapel im Kahn, von hinten nach vorn
sack(W * 0.890, H * 0.848, 190, 92, 6, 81)
sack(W * 0.715, H * 0.852, 200, 95, -5, 82, seal=True)
sack(W * 0.800, H * 0.835, 150, 190, 3, 83, upright=True, seal=True)
sack(W * 0.735, H * 0.892, 215, 102, 6, 84)
sack(W * 0.845, H * 0.885, 215, 102, -4, 85, seal=True)
sack(W * 0.920, H * 0.878, 150, 90, 12, 87)
front_hull()
# Kahn samt Ladung kleiner und weiter zurück setzen: er ist nur ein Hinweis
bm = (np.abs(img - pre_boat).sum(axis=2) > 0.004).astype(np.float32)
bm = cv2.morphologyEx(bm, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
k_ = 0.70; ax_, ay_ = W * 0.97, H * 0.955
M = np.float32([[k_, 0, ax_ * (1 - k_)], [0, k_, ay_ * (1 - k_) - H * 0.035]])
layer = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA)
lm = cv2.warpAffine(bm, M, (W, H), flags=cv2.INTER_LINEAR)
img = pre_boat
# Spiegelung im Wasser unter der Wasserlinie
wl_y = int(H * 0.940)
ref = np.zeros_like(layer); refm = np.zeros_like(lm)
hgt = H - wl_y
ref[wl_y:] = layer[wl_y - 1::-1][:hgt]; refm[wl_y:] = lm[wl_y - 1::-1][:hgt]
ref = cv2.GaussianBlur(ref, (0, 0), sigmaX=2, sigmaY=6); refm = cv2.GaussianBlur(refm, (0, 0), sigmaX=2, sigmaY=6)
img = blend(img, ref * 0.55 + C("#202825") * 0.45, refm * (1 - lm) * 0.6)
img = blend(img, layer, lm)
# ein paar verstreute Körner auf den Bohlen, manche grau
for k in range(160):
    fy = rng.uniform(0.80, 0.98)
    py = VP[1] + (H + 60 - VP[1]) * fy
    xl, _ = walk_x(py, -1); xr, _ = walk_x(py, 1)
    px = rng.uniform(xl + (xr - xl) * 0.55, xr - (xr - xl) * 0.12)
    grey = rng.random() < 0.3
    c = (C("#77786f") if grey else C("#bba878")) * (0.6 + 0.4 * rng.random())
    cv2.ellipse(img, (int(px), int(py)), (3, 2), float(rng.random() * 180), 0, 360, c.tolist(), -1, cv2.LINE_AA)

# ======================= Vordergrund-Schilf =======================
fg = img.copy()
reeds(fg, 520, (-60, W * 0.17), (H * 0.95, H * 1.06), (400, 1050), (3, 9), ("#12140c", "#3b3524"), 44, lean=(-0.02, 0.42), heads=0.45, tips="#8b7d55")
reeds(fg, 380, (W * 0.91, W + 60), (H * 0.95, H * 1.06), (380, 900), (3, 9), ("#12140c", "#3b3524"), 45, lean=(-0.30, 0.04), heads=0.45, tips="#8b7d55")
reeds(fg, 60, (W * 0.48, W * 0.62), (H * 0.99, H * 1.05), (110, 260), (2, 5), ("#16170f", "#4c4229"), 46, lean=(-0.2, 0.25), heads=0.3, tips="#9a8a5c")
reeds(fg, 120, (W * 0.15, W * 0.30), (H * 0.97, H * 1.05), (90, 260), (2, 4), ("#16170f", "#4c4229"), 47, lean=(-0.1, 0.3), heads=0.3, tips="#9a8a5c")
fgmask = (np.abs(fg - img).sum(axis=2) > 0.015).astype(np.float32)
img = blend(img, cv2.GaussianBlur(fg, (0, 0), 1.8), cv2.GaussianBlur(fgmask, (0, 0), 1.3))

# ======================= Dunst und Niesel =======================
fog = cv2.resize(noise(300, 5, 50, w=W, h=H // 4), (W, H))
band = np.exp(-((yy - (HZ + 8)) / (H * 0.060)) ** 2)
img = blend(img, C("#aaa894"), np.clip(band * (0.20 + 0.50 * fog), 0, 1) * 0.6)
band2 = np.exp(-((yy - H * 0.70) / (H * 0.045)) ** 2) * np.clip(1 - np.abs(xx - W * 0.33) / (W * 0.5), 0, 1)
img = blend(img, C("#8e8f7f"), np.clip(band2 * fog * 0.30, 0, 1))
# den Dorfumriss nach dem Dunst wieder etwas hervorholen, damit er lesbar bleibt
img = blend(img, village_layer, vil * 0.35)
rain = np.zeros((H, W), np.float32)
for k in range(2200):
    x0, y0 = rng.random() * W, rng.random() * H
    L = 16 + rng.random() * 26
    cv2.line(rain, (int(x0), int(y0)), (int(x0 - L * 0.22), int(y0 + L)), 1.0, 1, cv2.LINE_AA)
img = blend(img, C("#bdbcac"), cv2.GaussianBlur(rain, (0, 0), 0.7) * 0.07)

# ======================= Malerische Nachbearbeitung =======================
img = np.clip(img, 0, 1)


def strokes(src, n, length, width, seed, protect):
    """Pinselstriche entlang der Bildstruktur (Strukturtensor), Farbe aus dem geglätteten Bild."""
    r = np.random.default_rng(seed)
    g = cv2.cvtColor((src * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    gx_ = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=5); gy_ = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=5)
    jxx = cv2.GaussianBlur(gx_ * gx_, (0, 0), 9); jyy = cv2.GaussianBlur(gy_ * gy_, (0, 0), 9); jxy = cv2.GaussianBlur(gx_ * gy_, (0, 0), 9)
    theta = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2       # entlang der Kanten
    coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-3)
    smooth = cv2.GaussianBlur(src, (0, 0), width * 0.5)
    canvas = src.copy()
    for _ in range(n):
        x, y = int(r.random() * W), int(r.random() * H)
        if protect[y, x] > 0.2:
            continue
        a = theta[y, x] if coh[y, x] > 0.25 else (0.0 if y < HZ else np.pi / 2 * (1 if r.random() < 0.5 else 0))
        L = length * r.uniform(0.6, 1.3)
        dx, dy = np.cos(a) * L / 2, np.sin(a) * L / 2
        col = smooth[y, x] * r.uniform(0.94, 1.06)
        cv2.line(canvas, (int(x - dx), int(y - dy)), (int(x + dx), int(y + dy)), col.tolist(), int(max(1, width * r.uniform(0.7, 1.2))), cv2.LINE_AA)
    return canvas


sackzone = ((xx > W * 0.55) & (xx < W * 0.96) & (yy > H * 0.80) & (yy < H * 0.99)).astype(np.float32)
protect = np.clip(cv2.dilate(np.maximum(figs, vil), np.ones((9, 9), np.uint8)), 0, 1)
protect_fine = np.maximum(protect, sackzone * 0.0)
img = strokes(img, 160000, 26, 7, 91, np.maximum(protect, sackzone))
img = lerp(img, strokes(img, 220000, 12, 3, 92, protect), 0.7)
u8 = (img * 255).astype(np.uint8)
paint = cv2.xphoto.oilPainting(cv2.cvtColor(u8, cv2.COLOR_RGB2BGR), 6, 1, cv2.COLOR_BGR2Lab)
paint = cv2.cvtColor(paint, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
# Feinheiten (Gestalten, Siegel, Fenster) aus dem Original zurückholen
detail = np.maximum(np.maximum(figs, vil), sackzone * 0.5)
p = lerp(paint, img, np.clip(0.30 + 0.55 * cv2.GaussianBlur(detail, (0, 0), 3), 0, 1)[..., None])
p = blend(p, fig_col, figs_soft * 0.92)
# Pinselduktus: Helligkeitsmodulation entlang gerichteter Striche, im Himmel waagrecht, im Schilf senkrecht
bn = rng.random((H, W)).astype(np.float32)
kh = np.full((1, 31), 1 / 31, np.float32)
kvv = np.full((31, 1), 1 / 31, np.float32)
sh_ = cv2.filter2D(bn, -1, kh); sv_ = cv2.filter2D(bn, -1, kvv)
wv = np.clip((yy - HZ) / (H * 0.25), 0, 1)
sk = lerp(sh_, sv_, wv); sk = (sk - sk.mean()) / (sk.std() + 1e-6)
sk = cv2.GaussianBlur(sk, (0, 0), 0.8)
p *= (1 + 0.03 * sk[..., None])
# Leinwand (feines Gewebe aus Rauschen, keine Linien)
cv = noise(3, 2, 60) - 0.5
p *= (1 + 0.035 * cv[..., None])
# Farbstimmung: entsättigt, Schatten grünlich-kühl, Lichter warm
lum = p.mean(axis=2, keepdims=True)
p = lerp(lum, p, 0.80)
p += (C("#1d2b28") - lum) * (1 - lum) * 0.12 + (C("#efe0b0") - lum) * lum ** 2 * 0.10
# Tonwertkurve: etwas mehr Tiefe
p = np.clip(p, 0, 1) ** 1.08
# Vignette
v = 1 - 0.55 * (((xx - W * 0.48) / (W * 0.66)) ** 2 + ((yy - H * 0.56) / (H * 0.80)) ** 2)
p *= np.clip(v, 0.30, 1)[..., None]
p += rng.normal(0, 0.010, p.shape).astype(np.float32)
out = (np.clip(p, 0, 1) * 255).astype(np.uint8)
cv2.imwrite(OUT, cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 93])
print("ok", OUT)
