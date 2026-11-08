"""Zeichnet die Karten von „Graufieber“ (Loremaster- und Spielerfassung) und das Routendiagramm.

Helfer (rough, blob, label, num, frame …) übernommen aus tools/maps.py der Finsterwacht.

Optional step: the rendered JPGs are committed in assets/maps, so the PDF build
never needs this. Run it only after changing a map:

    pip install playwright pillow && playwright install chromium
    python3 tools/maps.py
"""
import random, math
from playwright.sync_api import sync_playwright

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "assets", "maps") + os.sep
SVG = os.path.join(D, "svg") + os.sep
INK, RED = "#3a2716", "#8a2e1e"
W, H = 800, 600
GM = True


def rough(pts, closed=False, jit=2.2, seg=14, seed=1):
    """Hand-drawn polyline: subdivide each segment and jitter the points."""
    r = random.Random(seed)
    P = pts + ([pts[0]] if closed else [])
    out = []
    for (x1, y1), (x2, y2) in zip(P, P[1:]):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / seg))
        for i in range(n):
            t = i / n
            out.append((x1 + (x2 - x1) * t + r.uniform(-jit, jit), y1 + (y2 - y1) * t + r.uniform(-jit, jit)))
    out.append(P[-1] if not closed else out[0])
    d = f"M{out[0][0]:.1f} {out[0][1]:.1f}"
    for (ax, ay), (bx, by) in zip(out, out[1:]):
        d += f" Q{ax:.1f} {ay:.1f} {(ax + bx) / 2:.1f} {(ay + by) / 2:.1f}"
    d += f" L{out[-1][0]:.1f} {out[-1][1]:.1f}"
    return d + (" Z" if closed else "")


def blob(cx, cy, rx, ry, irr=0.08, n=28, seed=1, a0=0, a1=360):
    r = random.Random(seed)
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        k = 1 + r.uniform(-irr, irr)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts


def path(d, w=1.6, col=INK, dash=None, fill="none", op=1):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="{fill}" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" opacity="{op}"{da}/>'


def label(x, y, txt, size=24, anchor="middle", rot=0, col=INK, style=""):
    tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
    return f'<text x="{x}" y="{y}" font-family="TeX Gyre Chorus" font-size="{size}" fill="{col}" text-anchor="{anchor}"{tr} {style}>{txt}</text>'


def num(x, y, n):
    if not GM:
        return ""
    return (f'<circle cx="{x}" cy="{y}" r="13" fill="#efe2c4" stroke="{RED}" stroke-width="1.6"/>'
            f'<text x="{x}" y="{y + 5.5}" font-family="TeX Gyre Pagella" font-weight="700" font-size="16" fill="{RED}" text-anchor="middle">{n}</text>')


def hachures(pts, out=True, length=12, every=1, seed=3, w=1.1):
    """Short strokes pointing outward from a polygon edge (cliffs, earthworks)."""
    r = random.Random(seed)
    s = ""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    for i, (x1, y1) in enumerate(pts[:-1]):
        x2, y2 = pts[i + 1]
        n = int(math.hypot(x2 - x1, y2 - y1) / 9)
        for j in range(0, n, every):
            t = j / max(n, 1)
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            dx, dy = x - cx, y - cy
            L = math.hypot(dx, dy) or 1
            k = length * r.uniform(0.6, 1.25) * (1 if out else -1)
            s += path(f"M{x:.1f} {y:.1f} L{x + dx / L * k:.1f} {y + dy / L * k:.1f}", w)
    return s


def trees(cx, cy, n, spread, seed):
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = cx + r.uniform(-spread, spread), cy + r.uniform(-spread * 0.6, spread * 0.6)
        s += path(rough([(x - 5, y + 4), (x, y - 6), (x + 5, y + 4)], jit=0.6, seg=5, seed=r.randint(0, 999)), 1.2)
    return s


def compass(x, y):
    return (f'<g transform="translate({x} {y})">'
            + path(rough([(0, -38), (7, 0), (0, 38), (-7, 0)], closed=True, jit=0.7, seg=8, seed=5), 1.4)
            + path("M0 -38 L7 0 L0 0 Z", 0.5, fill=INK, op=0.85)
            + path(rough([(-30, 0), (30, 0)], jit=0.6, seed=6), 1)
            + f'<text x="0" y="-44" font-family="TeX Gyre Pagella" font-weight="700" font-size="16" fill="{INK}" text-anchor="middle">N</text></g>')


def cartouche(x, y, title, sub, w=250):
    return (path(rough([(x, y), (x + w, y), (x + w, y + 64), (x, y + 64)], closed=True, jit=1.2, seed=9), 1.5, fill="#efe2c4", op=0.95)
            + path(rough([(x + 6, y + 6), (x + w - 6, y + 6), (x + w - 6, y + 58), (x + 6, y + 58)], closed=True, jit=0.9, seed=10), 0.8)
            + label(x + w / 2, y + 33, title, 30, col=RED)
            + label(x + w / 2, y + 52, sub, 17))


def frame(content, seed):
    r = random.Random(seed)
    edge = []
    for (x1, y1), (x2, y2) in zip([(6, 6), (W - 6, 6), (W - 6, H - 6), (6, H - 6)], [(W - 6, 6), (W - 6, H - 6), (6, H - 6), (6, 6)]):
        n = 40
        for i in range(n):
            t = i / n
            edge.append((x1 + (x2 - x1) * t + r.uniform(-3.5, 3.5), y1 + (y2 - y1) * t + r.uniform(-3.5, 3.5)))
    clip = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in edge) + " Z"
    stains = "".join(
        f'<circle cx="{r.uniform(60, W - 60):.0f}" cy="{r.uniform(60, H - 60):.0f}" r="{r.uniform(30, 90):.0f}" fill="url(#stain)" opacity="{r.uniform(0.25, 0.55):.2f}"/>'
        for _ in range(6))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 2}" height="{H * 2}">
<defs>
 <clipPath id="torn"><path d="{clip}"/></clipPath>
 <filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" seed="{seed}"/>
  <feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.25  0 0 0 0 0.12  0 0 0 0.22 0"/>
 </filter>
 <filter id="blot" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="4" seed="{seed + 3}"/>
  <feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.32  0 0 0 0 0.15  0 0 0 0.55 -0.12"/>
 </filter>
 <filter id="ink" x="-5%" y="-5%" width="110%" height="110%">
  <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="{seed + 7}" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="3" xChannelSelector="R" yChannelSelector="G"/>
 </filter>
 <radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset="55%" stop-color="#e8d8b3" stop-opacity="0"/><stop offset="100%" stop-color="#7a5528" stop-opacity="0.55"/></radialGradient>
 <radialGradient id="stain"><stop offset="0%" stop-color="#b08850" stop-opacity="0"/><stop offset="80%" stop-color="#a07840" stop-opacity="0.25"/><stop offset="100%" stop-color="#8a6230" stop-opacity="0"/></radialGradient>
 <radialGradient id="lamp"><stop offset="0%" stop-color="#e8a33a" stop-opacity="0.95"/><stop offset="100%" stop-color="#e8a33a" stop-opacity="0"/></radialGradient>
 <radialGradient id="pale"><stop offset="0%" stop-color="#cfe3e6" stop-opacity="1"/><stop offset="100%" stop-color="#9fc4cc" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="#ffffff"/>
<g clip-path="url(#torn)">
 <rect width="{W}" height="{H}" fill="#e9dbb9"/>
 <rect width="{W}" height="{H}" filter="url(#blot)"/>
 {stains}
 <g filter="url(#ink)" opacity="0.92">{content}</g>
 <rect width="{W}" height="{H}" filter="url(#grain)"/>
 <rect width="{W}" height="{H}" fill="url(#vig)"/>
</g>
<path d="{clip}" fill="none" stroke="#6b4a24" stroke-width="1.2" opacity="0.5"/>
</svg>'''




BROWN = "#6b4a24"
WATER = "#c9c8b0"


def reeds(cx, cy, n, sx, sy, seed, col=INK, w=0.9):
    """Schilfbüschel: kurze, leicht geneigte Striche mit Kolben."""
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = cx + r.uniform(-sx, sx), cy + r.uniform(-sy, sy)
        h = r.uniform(9, 16)
        lean = r.uniform(-3, 3)
        s += path(f"M{x:.1f} {y:.1f} Q{x + lean / 2:.1f} {y - h / 2:.1f} {x + lean:.1f} {y - h:.1f}", w, col=col)
        if r.random() < 0.35:
            s += f'<ellipse cx="{x + lean:.1f}" cy="{y - h:.1f}" rx="1.3" ry="2.8" fill="{col}" transform="rotate({lean * 4:.0f} {x + lean:.1f} {y - h:.1f})"/>'
    return s


def waves(x0, y0, x1, y1, n, seed, op=0.45):
    """Wasser: kurze Wellenstriche verteilt über ein Rechteck."""
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        L = r.uniform(10, 22)
        s += path(f"M{x:.1f} {y:.1f} q{L / 4:.1f} -3 {L / 2:.1f} 0 t{L / 2:.1f} 0", 0.8, op=op)
    return s


def willows(cx, cy, n, spread, seed):
    """Weiden: runde Krone mit hängenden Strichen."""
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = cx + r.uniform(-spread, spread), cy + r.uniform(-spread * 0.6, spread * 0.6)
        s += path(rough(blob(x, y, 9, 7, irr=0.15, n=10, seed=r.randint(0, 999), a0=180, a1=360), jit=0.6, seg=4, seed=r.randint(0, 999)), 1.1)
        for k in range(4):
            dx = -7 + k * 4.6
            s += path(f"M{x + dx:.1f} {y - 2:.1f} q1 6 {r.uniform(-1, 1):.1f} {r.uniform(9, 13):.1f}", 0.8)
    return s


def house(x, y, w, h, seed, fill="#d9c69e", lw=2.2):
    return path(rough([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], closed=True, jit=1.0, seed=seed), lw, fill=fill)


# ---------------- Der Weidenhof ----------------
def weidenhof():
    s = ""
    # Felder im Südwesten und Osten (Furchen)
    for k in range(9):
        s += path(rough([(40, 470 + k * 13), (190, 452 + k * 13)], jit=1.0, seed=600 + k), 0.7, op=0.5)
    for k in range(8):
        s += path(rough([(640, 110 + k * 14), (770, 98 + k * 14)], jit=1.0, seed=620 + k), 0.7, op=0.5)
    # Mauer mit eingestürztem Stück im Norden (x 330–420)
    segs = [[(420, 140), (600, 142), (612, 300), (606, 452), (430, 450)],
            [(372, 450), (212, 446), (206, 300), (220, 140), (330, 140)]]
    for i, sg in enumerate(segs):
        s += path(rough(sg, jit=1.0, seed=640 + i), 4.0) + path(rough(sg, jit=1.0, seed=640 + i), 1, col="#e9dbb9")
    rr = random.Random(645)
    s += "".join(f'<circle cx="{rr.uniform(332, 418):.0f}" cy="{rr.uniform(134, 150):.0f}" r="{rr.uniform(1.4, 3.2):.1f}" fill="{INK}"/>' for _ in range(18))
    s += label(300, 124, "eingestürzt", 16, col=BROWN)
    # Tor im Süden
    for gx in (378, 424):
        s += house(gx - 7, 440, 14, 18, int(gx), lw=1.6)
    s += path(rough([(385, 449), (417, 449)], jit=0.5, seed=650), 1.0, dash="3 3")
    s += num(356, 486, 1) + label(440, 492, "Tor", 20, anchor="start")
    # Scheune
    s += house(240, 190, 140, 100, 660)
    for k in range(5):
        s += path(rough([(252 + k * 26, 200), (252 + k * 26, 280)], jit=0.6, seed=661 + k), 0.6, op=0.6)
    s += label(310, 316, "Scheune", 21) + num(310, 168, 2)
    # Haupthaus mit Schreibstube
    s += house(450, 185, 130, 92, 670)
    s += path(rough([(515, 185), (515, 277)], jit=0.6, seed=671), 1.0)
    s += label(515, 304, "Haupthaus", 21) + num(515, 164, 3)
    if GM:
        s += label(482, 236, "Schreib-", 14) + label(482, 251, "stube", 14)
        # Keller: Treppe und gestrichelter Raum unter dem Haus
        for k in range(4):
            s += path(f"M{548 + k * 4} {244 + k * 5} l14 0", 1.1)
        s += path(rough([(530, 228), (574, 228), (574, 270), (530, 270)], closed=True, jit=0.6, seed=672), 1.1, dash="4 3", col=RED)
        s += num(626, 252, 4) + label(642, 246, "Keller", 17, anchor="start") + label(642, 264, "(unter dem Haus)", 14, anchor="start", col=BROWN)
    # Brunnen
    s += f'<circle cx="420" cy="368" r="10" fill="none" stroke="{INK}" stroke-width="1.6"/><circle cx="420" cy="368" r="3.8" fill="{INK}"/>'
    s += label(446, 374, "Brunnen", 17, anchor="start") + num(392, 350, 5)
    # Pferch und Karren im Hof
    s += path(rough([(260, 360), (340, 360), (340, 420), (260, 420)], closed=True, jit=1.0, seed=680), 1.0, dash="2 3")
    s += label(300, 395, "Pferch", 16, col=BROWN)
    # Weg nach Osten zur Furt
    s += path(rough([(401, 460), (430, 520), (560, 548), (700, 540), (790, 520)], jit=1.3, seed=690), 1.2)
    s += path(rough([(420, 458), (450, 512), (566, 534), (700, 526), (790, 506)], jit=1.3, seed=691), 1.2)
    s += label(760, 500, "nach Brandhafen · ½ Tag", 17, anchor="end")
    # Schleichweg über die eingestürzte Mauer
    if GM:
        s += path(rough([(360, 40), (366, 90), (378, 140), (392, 220), (398, 320)], jit=0.8, seed=700), 1.2, dash="4 4", col=RED)
        s += label(372, 40, "über die Mauer (Stealth)", 15, anchor="start", col=RED)
    s += willows(110, 220, 10, 60, 710) + willows(700, 380, 8, 50, 711) + willows(130, 380, 5, 40, 712)
    s += compass(735, 92)
    s += cartouche(28, 24, "Der Weidenhof", "Lager der Helfer, Halimath TA 2979" if GM else "von der Weidenreihe aus gesehen", 280)
    s += label(772, 588, "Skizze für den Loremaster · nicht maßstabsgetreu" if GM else "Kohle auf Rinde, eilig gezeichnet", 15, anchor="end", col=BROWN)
    return frame(s, 41)


# ---------------- Die Reiherinsel ----------------
def reiherinsel():
    s = ""
    s += f'<rect x="0" y="0" width="{W}" height="{H}" fill="{WATER}" opacity="0.35"/>'
    s += waves(20, 110, 780, 580, 110, 800)
    isle = blob(410, 320, 215, 140, irr=0.09, n=34, seed=801)
    s += path(rough(isle, closed=True, jit=1.6, seed=802), 1.8, fill="#e3d2ab")
    # Schilf rund um die Insel, dicht im Norden
    for k, (x, y) in enumerate(isle[::2]):
        s += reeds(x, y, 7, 14, 10, 810 + k)
    s += reeds(410, 168, 70, 150, 26, 850) + reeds(180, 240, 30, 50, 40, 851) + reeds(660, 420, 26, 50, 36, 852)
    s += label(410, 132, "Schilfgürtel", 21, col=BROWN)
    # Turmruine
    s += f'<circle cx="430" cy="292" r="34" fill="#d9c69e" stroke="{INK}" stroke-width="2.4"/>'
    s += path(rough(blob(430, 292, 20, 20, irr=0.1, n=16, seed=860, a0=40, a1=320), jit=0.8, seed=861), 1.3)
    s += label(430, 352, "Turmruine", 20)
    # Hütten der Wachen
    s += house(300, 300, 34, 24, 870, lw=1.6) + house(500, 372, 30, 22, 871, lw=1.6)
    # Wachfeuer
    s += f'<circle cx="345" cy="398" r="20" fill="url(#lamp)"/>'
    s += path(rough([(337, 404), (345, 386), (353, 404)], closed=True, jit=0.5, seg=5, seed=880), 1.2, fill="#a8541a")
    s += label(368, 404, "Wachfeuer", 18, anchor="start")
    # Steg im Süden mit Booten
    s += path(rough([(398, 455), (398, 545)], jit=0.5, seed=890), 1.6) + path(rough([(418, 455), (418, 545)], jit=0.5, seed=891), 1.6)
    for k in range(9):
        s += path(f"M398 {462 + k * 9} L418 {462 + k * 9}", 0.9)
    for k, (bx, by) in enumerate([(372, 520), (446, 506)]):
        s += path(rough([(bx - 18, by), (bx + 18, by), (bx + 10, by + 9), (bx - 10, by + 9)], closed=True, jit=0.6, seg=6, seed=895 + k), 1.3, fill="#cdb78c")
    s += f'<circle cx="420" cy="548" r="11" fill="url(#lamp)"/><circle cx="420" cy="548" r="2.6" fill="#a8541a"/>'
    s += label(440, 572, "Steg", 20, anchor="start")
    if GM:
        s += num(470, 548, 1) + num(345, 440, 2) + num(560, 168, 3) + num(386, 266, 4)
        # verborgener Zugang durch das Schilf
        s += path(rough([(470, 24), (452, 90), (470, 150), (448, 210), (440, 256)], jit=0.8, seed=900), 1.2, dash="4 4", col=RED)
        s += label(486, 40, "verborgener Zugang", 16, anchor="start", col=RED)
        # Gewölbe unter dem Turm
        s += path(rough([(464, 270), (490, 255)], jit=0.4, seed=905), 1.0, dash="4 4", col=RED)
        s += path(rough([(490, 230), (594, 230), (594, 282), (490, 282)], closed=True, jit=0.6, seed=906), 1.2, dash="4 3", col=RED)
        s += path(rough([(530, 282), (594, 282), (594, 318), (530, 318)], closed=True, jit=0.6, seed=907), 1.2, dash="4 3", col=RED)
        s += label(542, 262, "Fieberküche", 15) + num(478, 214, 5)
        s += label(562, 305, "Truhe", 14) + num(614, 298, 6)
        s += label(548, 344, "Gewölbe (unter der Erde)", 13, col=BROWN)
    s += compass(735, 470)
    s += cartouche(28, 24, "Die Reiherinsel", "in den Grauen Marschen · Halimath TA 2979" if GM else "wie Thalmir sie beschrieb", 280)
    s += label(772, 588, "Skizze für den Loremaster · nicht maßstabsgetreu" if GM else "", 15, anchor="end", col=BROWN)
    return frame(s, 53)


# ---------------- Brandhafen und die Grauen Marschen (nur Spieler) ----------------
def brandhafen():
    s = ""
    MI = 18  # Karteneinheiten je Meile: Brandhafen – Reiherinsel etwa 20 Meilen
    # Küste: Land oben, die Bucht von Belfalas unten
    coast = [(0, 410), (90, 420), (180, 400), (260, 420), (300, 440), (340, 426), (420, 400),
             (520, 404), (620, 396), (720, 410), (800, 400)]
    sea = coast + [(800, 600), (0, 600)]
    s += path(rough(sea, closed=True, jit=1.2, seed=1100), 0.1, fill=WATER, op=0.45)
    s += path(rough(coast, jit=1.6, seed=1101), 1.8)
    s += waves(20, 470, 780, 580, 70, 1102)
    s += label(560, 540, "Bucht von Belfalas", 30, col=BROWN)
    # Graue Marschen: Lagune hinter einer Nehrung östlich des Ortes
    lagoon = blob(590, 352, 200, 44, irr=0.16, n=30, seed=1103)
    s += path(rough(lagoon, closed=True, jit=1.4, seed=1104), 1.0, fill=WATER, op=0.6)
    s += reeds(590, 340, 120, 190, 40, 1105) + reeds(470, 300, 25, 50, 20, 1106) + reeds(720, 300, 25, 50, 20, 1107)
    for k in range(6):
        s += path(rough([(420 + k * 60, 330 + (k % 2) * 30), (460 + k * 60, 360 + (k % 3) * 10)], jit=1.2, seed=1110 + k), 0.8, op=0.7)
    s += label(600, 268, "die Grauen Marschen", 26)
    # Brandbach von Norden in den Hafen
    s += path(rough([(390, 0), (350, 120), (300, 260), (300, 360), (304, 432)], jit=1.4, seed=1120), 1.3)
    s += path(rough([(406, 0), (366, 120), (316, 260), (316, 360), (322, 432)], jit=1.4, seed=1121), 1.3)
    s += label(318, 220, "Brandbach", 18, rot=-62)
    # Brandhafen: Mole, Ruinen, Hafenturm
    s += path(rough([(322, 436), (352, 470), (372, 472)], jit=0.8, seed=1130), 3.0)
    for k, (x, y) in enumerate([(330, 392), (346, 404), (276, 400), (288, 386), (340, 376), (262, 418)]):
        s += house(x - 6, y - 5, 12, 10, 1131 + k, lw=1.2)
    s += f'<circle cx="374" cy="470" r="6" fill="#d9c69e" stroke="{INK}" stroke-width="1.6"/>'
    s += label(180, 296, "Brandhafen", 26) + label(180, 314, "ein Fischerdorf", 15, col=BROWN)
    s += path(rough([(200, 322), (250, 352), (270, 384)], jit=0.6, seed=1135), 0.8, dash="2 3")
    # Nachbardörfer an der Küste
    for k, (x, y) in enumerate([(104, 404), (116, 398), (126, 408)]):
        s += house(x - 5, y - 4, 10, 8, 1170 + k, lw=1.1)
    s += label(116, 440, "Kiesbucht", 17)
    for k, (x, y) in enumerate([(700, 396), (712, 390), (722, 400)]):
        s += house(x - 5, y - 4, 10, 8, 1175 + k, lw=1.1)
    s += label(712, 440, "Möwenhaken", 17)
    # Küstenstraße von Dol Amroth nach Linhir, über die Furt
    road = [(0, 330), (120, 345), (220, 365), (306, 372), (400, 300), (520, 240), (660, 220), (800, 200)]
    s += path(rough(road, jit=1.2, seed=1140), 1.2) + path(rough([(x, y + 12) for x, y in road], jit=1.2, seed=1141), 1.2)
    s += label(20, 372, "nach Dol Amroth", 17, anchor="start") + label(785, 186, "nach Linhir", 17, anchor="end")
    s += path(rough([(296, 368), (322, 374)], jit=0.4, seed=1142), 1.0, dash="2 2")
    # Weidenhof landeinwärts
    s += house(150, 196, 18, 14, 1150, lw=1.4)
    s += path(rough([(168, 206), (230, 260), (300, 368)], jit=1.0, seed=1151), 1.0, dash="4 4")
    s += label(160, 186, "Weidenhof", 17) + willows(120, 240, 5, 30, 1152)
    s += label(470, 110, "Belfalas", 32, col=BROWN)
    s += trees(620, 110, 9, 50, 1160) + trees(90, 110, 8, 40, 1161) + willows(480, 180, 5, 40, 1162)
    # Maßstab
    x0, y0 = 40, 552
    s += path(f"M{x0} {y0} L{x0 + 10 * MI} {y0}", 1.6)
    for m in (0, 5, 10):
        s += path(f"M{x0 + m * MI} {y0 - 6} L{x0 + m * MI} {y0 + 6}", 1.4)
        s += label(x0 + m * MI, y0 + 22, f"{m}", 15)
    s += path(f"M{x0} {y0} L{x0 + 5 * MI} {y0}", 4, op=0.8)
    s += label(x0 + 10 * MI + 12, y0 + 5, "Meilen", 15, anchor="start")
    s += compass(745, 520)
    s += cartouche(28, 24, "Brandhafen", "und die Grauen Marschen, wie Tobbe sie beschreibt", 330)
    return frame(s, 67)


# ---------------- Routendiagramm (Überblick) ----------------
def route():
    """Senkrechter Stapel der Stationen, Reisezeiten an den Pfeilen, Höhepunkt rot,
    Rhaskars Verfolgung gestrichelt rot. Sauber gezeichnet, nicht von Hand."""
    font = "font-family=\"TeX Gyre Pagella\""
    grey, line, red, ink = "#6f665c", "#9a9088", "#7a2a1f", "#2b2420"
    bw, bh, gap, x0, top = 250, 40, 22, 40, 12
    stages = [("Nach Süden", "Auftrag des Truchsess · Pelargir · Linhir"),
              ("Brandhafen", "Mardion · Aldis · die Räumung"),
              ("Die Schilfbrüder", "Vertrauen · Fieberrinde · ein Boot"),
              ("Die Lager", "Furtlager oder Weidenhof · Beweise"),
              ("Fahrt zur Reiherinsel", "Graue Marschen · ein Tag"),
              ("Das Labor", "Fieberküche · Zâkarûns Truhe"),
              ("Die Wahl", "Mardion, Aldis oder Hedra")]
    legs = ["neun Tage", "nächster Morgen", "Reihenfolge frei", "sofort", "ein Tag", "Rückfahrt, ein Tag"]
    Hs = top * 2 + len(stages) * bh + (len(stages) - 1) * gap
    Ws = 420
    cx = x0 + bw / 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Ws} {Hs}" width="{Ws * 4}" height="{Hs * 4}">',
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           f'<path d="M0 0L10 5L0 10z" fill="{line}"/></marker>'
           '<marker id="r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           f'<path d="M0 0L10 5L0 10z" fill="{red}"/></marker></defs>',
           f'<rect width="{Ws}" height="{Hs}" fill="#ffffff"/>']
    ys = [top + i * (bh + gap) for i in range(len(stages))]
    for i, ((name, sub), y) in enumerate(zip(stages, ys)):
        climax = name == "Das Labor"
        out.append(f'<rect x="{x0}" y="{y}" width="{bw}" height="{bh}" rx="8" fill="{"#f6e7e3" if climax else "#f7f1e6"}" '
                   f'stroke="{red if climax else line}" stroke-width="{1.8 if climax else 1.1}"/>')
        out.append(f'<text x="{cx}" y="{y + 17}" {font} font-weight="700" font-size="13.5" fill="{red if climax else ink}" text-anchor="middle">{name}</text>')
        out.append(f'<text x="{cx}" y="{y + 32}" {font} font-size="10.5" fill="{grey}" text-anchor="middle">{sub}</text>')
        if i < len(legs):
            out.append(f'<path d="M{cx} {y + bh} V{y + bh + gap - 2}" stroke="{line}" stroke-width="1.2" marker-end="url(#a)"/>')
            out.append(f'<text x="{cx + 8}" y="{y + bh + gap / 2 + 4}" {font} font-style="italic" font-size="10.5" fill="{grey}">{legs[i]}</text>')
    # Verfolgung: von den Lagern zur Insel
    y3, y5 = ys[3] + bh / 2, ys[5] + bh / 2
    px = x0 + bw + 50
    out.append(f'<path d="M{x0 + bw} {y3} H{px} V{y5} H{x0 + bw + 3}" fill="none" stroke="{red}" stroke-width="1.2" stroke-dasharray="5 4" marker-end="url(#r)"/>')
    out.append(f'<text x="{px + 8}" y="{(y3 + y5) / 2 - 4}" {font} font-style="italic" font-size="11" fill="{red}">Rhaskar</text>')
    out.append(f'<text x="{px + 8}" y="{(y3 + y5) / 2 + 10}" {font} font-style="italic" font-size="11" fill="{red}">verfolgt</text>')
    out.append("</svg>")
    return "\n".join(out), Ws * 4, Hs * 4


if __name__ == "__main__":
    os.makedirs(SVG, exist_ok=True)
    jobs = []
    for gm in (True, False):
        GM = gm
        suf = "" if gm else "-players"
        jobs += [("map-weidenhof" + suf, weidenhof()), ("map-reiherinsel" + suf, reiherinsel())]
    GM = False
    jobs.append(("map-brandhafen-players", brandhafen()))
    from PIL import Image
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W * 2, "height": H * 2})
        for name, svg in jobs:
            open(SVG + name + "-de.svg", "w").write(svg)
            pg.set_content(f'<html><body style="margin:0;background:#fff">{svg}</body></html>', wait_until="load")
            pg.screenshot(path=D + name + "-de.png", clip={"x": 0, "y": 0, "width": W * 2, "height": H * 2})
        svg, rw, rh = route()
        open(os.path.join(ROOT, "assets", "route-de.svg"), "w").write(svg)
        pg.set_viewport_size({"width": rw, "height": rh})
        pg.set_content(f'<html><body style="margin:0;background:#fff">{svg}</body></html>', wait_until="load")
        pg.screenshot(path=os.path.join(ROOT, "assets", "route-de.png"), clip={"x": 0, "y": 0, "width": rw, "height": rh})
        b.close()
    for name, _ in jobs:
        Image.open(D + name + "-de.png").convert("RGB").save(D + name + "-de.jpg", quality=88)
        os.remove(D + name + "-de.png")
    print("ok")
