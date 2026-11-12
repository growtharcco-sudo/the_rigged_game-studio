"""Noir paper-cutout renderer for The Rigged Game (spec -> video). The look is ported unchanged from the
hand-made episodes in legacy/ (EP01 Monte Carlo, EP02 No clocks, EP02 countdown).

A spec has scenes; each scene is a list of elements drawn in order. Elements carry beat-based timing:
  "at":   beat index when the element starts (-1 = already fully visible at frame 0)
  "delay": seconds after that beat; "until": beat index where it fades out
  any "<name>_at" field: another moment, same format (beat int, [beat, delay], {"b":beat,"w":word,"d":sec},
         or "end" / ["end", delay] = after the last spoken word)
Drawers get lt (seconds since the element started) and R(name) (seconds since <name>_at).
Coordinates live in pipeline/kit.py; this file only knows how to draw each element type.
"""
import math, os, random, subprocess, sys
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
CAP_Y = 1440
XF = 0.25  # crossfade between scenes

# ---------------- basics ----------------
TF = {n: skia.Typeface.MakeFromFile(os.path.join(HERE, 'fonts', f'{n}.ttf')) for n in
      ['Inter-Black', 'Inter-Bold', 'Inter-Regular', 'Playfair-Black', 'Playfair-Bold', 'Mono-Bold']}

def C(hexs, a=255):
    hexs = hexs.lstrip('#')
    return skia.Color(int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16), a)

def font(name, size):
    f = skia.Font(TF[name], size); f.setEdging(skia.Font.Edging.kAntiAlias); f.setSubpixel(True)
    return f

def text_w(text, fname, size): return font(fname, size).measureText(text)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back_out(x, s=1.7):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def prog(t, a, b): return clamp((t - a) / (b - a))

def paint(color, a=None, style='fill', sw=0, blur=0):
    p = skia.Paint(AntiAlias=True)
    col = C(color) if isinstance(color, str) else color
    if a is not None: col = skia.ColorSetA(col, int(clamp(a) * 255))
    p.setColor(col)
    if style == 'stroke':
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(sw)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

def text_c(cv, s, x, y, f, p):
    w = f.measureText(s); cv.drawString(s, x - w / 2, y, f, p); return w

def glow(cv, x, y, r, color, a=0.5):
    p = skia.Paint(); col = C(color)
    p.setShader(skia.GradientShader.MakeRadial((x, y), r, [skia.ColorSetA(col, int(255 * a)), skia.ColorSetA(col, 0)]))
    cv.drawCircle(x, y, r, p)

def rect_path(l, t, r, b): p = skia.Path(); p.addRect(skia.Rect(l, t, r, b)); return p
def circ_path(x, y, r): p = skia.Path(); p.addCircle(x, y, r); return p

def cut(cv, path, color, dx=10, dy=14, sh=0.45):
    """paper cut-out layer: soft drop shadow then flat fill"""
    s = skia.Path(path); s.offset(dx, dy)
    cv.drawPath(s, paint('#000000', sh, blur=9)); cv.drawPath(path, paint(color))

# palette
PAPER = '#f6ecd4'; INKD = '#1a100b'; BROWN = '#6b4630'; RUST = '#b3261e'; AMBER = '#e8b04a'
SHADOW = '#050302'; GROUND = '#1a100b'; GOLD = '#ffcf5a'; GREEN = '#2f5a3a'; RED = '#c8342b'
BLACK = '#141414'; FELT = '#1f7a4a'; INK = '#2a2118'; CREAM = '#f4ead2'
BP = '#16477a'; BP_LINE = '#eaf4ff'; BP_HI = '#ffcf5a'
COLORS = {'paper': PAPER, 'ink': INKD, 'rust': RUST, 'gold': GOLD, 'amber': AMBER, 'green': GREEN, 'brown': BROWN}
def col(c): return COLORS.get(c, c)

R0 = random.Random(5)
PAPER_FIBERS = [(R0.uniform(0, W), R0.uniform(0, H), R0.uniform(30, 140), R0.uniform(0, 3.14)) for _ in range(160)]

def paper_bg(cv, top='#efe2c4', bot='#d9c49b'):
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, H)], [C(top), C(bot)]))
    cv.drawRect(skia.Rect(0, 0, W, H), p)
    for x, y, l, a in PAPER_FIBERS:
        cv.drawLine(x, y, x + math.cos(a) * l, y + math.sin(a) * l, paint('#8a6a3a', 0.05, 'stroke', 2))
    v = skia.Paint()
    v.setShader(skia.GradientShader.MakeRadial((W / 2, H * 0.45), H * 0.8,
                [skia.Color(0, 0, 0, 0), skia.Color(40, 20, 0, 0), skia.Color(40, 20, 0, 150)], [0, 0.5, 1]))
    cv.drawRect(skia.Rect(0, 0, W, H), v)

# ---------------- shapes ported from the episodes ----------------
ORDER = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33,
         1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]

def wedge_path(cx, cy, r0, r1, a0, a1):
    p = skia.Path()
    p.arcTo(skia.Rect(cx - r1, cy - r1, cx + r1, cy + r1), a0, a1 - a0, True)
    p.arcTo(skia.Rect(cx - r0, cy - r0, cx + r0, cy + r0), a1, a0 - a1, False)
    p.close(); return p

def wheel(cv, cx, cy, R, rot, highlight=None, hl_amt=0.0, dividers=1.0, flash=0.0):
    s = R / 300.0
    cv.drawCircle(cx, cy + 14 * s, R * 1.08, paint('#000000', 0.5, blur=20 * s))
    rim = skia.Paint(AntiAlias=True)
    rim.setShader(skia.GradientShader.MakeRadial((cx - R * 0.3, cy - R * 0.3), R * 1.6, [C('#7a4a22'), C('#3b210e'), C('#1e1006')]))
    cv.drawCircle(cx, cy, R * 1.08, rim)
    cv.drawCircle(cx, cy, R * 1.08, paint('#e2b84a', 0.8, 'stroke', 4 * s))
    cv.drawCircle(cx, cy, R * 0.98, paint('#120a04'))
    step = 360 / 37
    for i, num in enumerate(ORDER):
        a0 = rot + i * step - 90 - step / 2
        c = FELT if num == 0 else (RED if i % 2 == 1 else BLACK)
        cv.drawPath(wedge_path(cx, cy, R * 0.62, R * 0.95, a0, a0 + step), paint(c))
        if highlight and num in highlight and hl_amt > 0:
            cv.drawPath(wedge_path(cx, cy, R * 0.62, R * 0.95, a0, a0 + step), paint('#e2b84a', 0.85 * hl_amt))
        am = math.radians(a0 + step / 2)
        cv.save(); cv.translate(cx + math.cos(am) * R * 0.85, cy + math.sin(am) * R * 0.85); cv.rotate(a0 + step / 2 + 90)
        f = skia.Font(TF['Inter-Bold'], 22 * s); lab = str(num)
        tc = INK if (highlight and num in highlight and hl_amt > 0.5) else CREAM
        cv.drawString(lab, -f.measureText(lab) / 2, 8 * s, f, paint(tc)); cv.restore()
        a = math.radians(a0)
        cv.drawLine(cx + math.cos(a) * R * 0.62, cy + math.sin(a) * R * 0.62, cx + math.cos(a) * R * 0.95, cy + math.sin(a) * R * 0.95,
                    paint('#e2b84a' if flash <= 0 else '#ffffff', 0.7 * dividers + 0.3 * flash, 'stroke', (2 + 3 * flash) * s))
    cv.drawCircle(cx, cy, R * 0.62, paint('#e2b84a', 0.9, 'stroke', 3 * s))
    cone = skia.Paint(AntiAlias=True)
    cone.setShader(skia.GradientShader.MakeRadial((cx - R * 0.15, cy - R * 0.15), R * 0.7, [C('#8a5a2c'), C('#4a2a10'), C('#24140a')]))
    cv.drawCircle(cx, cy, R * 0.6, cone)
    for k in range(4):
        a = math.radians(rot + k * 90)
        cv.drawLine(cx, cy, cx + math.cos(a) * R * 0.32, cy + math.sin(a) * R * 0.32, paint('#e2b84a', 1, 'stroke', 10 * s))
        cv.drawCircle(cx + math.cos(a) * R * 0.32, cy + math.sin(a) * R * 0.32, 11 * s, paint('#e2b84a'))
    cv.drawCircle(cx, cy, 30 * s, paint('#e2b84a')); cv.drawCircle(cx, cy, 30 * s, paint('#fff3c4', 0.6, 'stroke', 3 * s))
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeLinear([(cx - R, cy - R), (cx + R, cy + R)],
                 [skia.Color(255, 255, 255, 40), skia.Color(255, 255, 255, 0), skia.Color(0, 0, 0, 60)]))
    cv.drawCircle(cx, cy, R * 1.08, sh)

def gear_path(cx, cy, r, teeth, rot, depth=0.16):
    p = skia.Path(); n = teeth * 4
    for i in range(n + 1):
        a = math.radians(rot) + 2 * math.pi * i / n
        rr = r if (i % 4) in (0, 1) else r * (1 - depth)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        p.moveTo(x, y) if i == 0 else p.lineTo(x, y)
    p.close(); p.addCircle(cx, cy, r * 0.35); p.setFillType(skia.PathFillType.kEvenOdd)
    return p

def man_path(x, y, s):
    """the channel's gambler: top hat, coat, cane"""
    p = skia.Path()
    p.moveTo(x - 150 * s, y + 520 * s)
    p.cubicTo(x - 160 * s, y + 250 * s, x - 120 * s, y + 140 * s, x - 60 * s, y + 120 * s)
    p.lineTo(x + 60 * s, y + 120 * s)
    p.cubicTo(x + 120 * s, y + 140 * s, x + 160 * s, y + 250 * s, x + 150 * s, y + 520 * s); p.close()
    p.addCircle(x, y + 60 * s, 62 * s)
    p.addRect(skia.Rect(x - 95 * s, y + 5 * s, x + 95 * s, y + 25 * s))
    p.addRect(skia.Rect(x - 58 * s, y - 120 * s, x + 58 * s, y + 10 * s))
    p.addRect(skia.Rect(x + 175 * s, y + 250 * s, x + 187 * s, y + 520 * s))
    p.setFillType(skia.PathFillType.kWinding); return p

def casino_sil(cx, base, sc):
    p = skia.Path()
    def rect(x, y, w, h): p.addRect(skia.Rect(cx + x * sc, base + y * sc, cx + (x + w) * sc, base + (y + h) * sc))
    rect(-430, -300, 860, 300)
    for tx in (-430, 330):
        rect(tx, -470, 100, 470)
        q = skia.Path(); q.moveTo(cx + tx * sc, base - 470 * sc)
        q.quadTo(cx + (tx + 50) * sc, base - 600 * sc, cx + (tx + 100) * sc, base - 470 * sc); q.close(); p.addPath(q)
        rect(tx + 47, -650, 6, 80)
    rect(-180, -380, 360, 380)
    q = skia.Path(); q.moveTo(cx - 180 * sc, base - 380 * sc)
    q.cubicTo(cx - 170 * sc, base - 560 * sc, cx + 170 * sc, base - 560 * sc, cx + 180 * sc, base - 380 * sc); q.close()
    p.addPath(q); p.setFillType(skia.PathFillType.kWinding); return p

def casino_windows(cv, cx, base, sc, color, a=1.0):
    for wx in list(range(-400, -200, 70)) + list(range(220, 400, 70)) + [-130, -40, 50]:
        top = -250 if abs(wx) > 180 else -330; hh = 170 if abs(wx) > 180 else 240
        cv.drawRoundRect(skia.Rect(cx + (wx + 10) * sc, base + top * sc, cx + (wx + 54) * sc, base + (top + hh) * sc), 22 * sc, 22 * sc, paint(color, a))

def palm(x, base, s):
    p = skia.Path()
    p.moveTo(x - 10 * s, base); p.quadTo(x + 30 * s, base - 250 * s, x + 10 * s, base - 480 * s)
    p.lineTo(x + 26 * s, base - 480 * s); p.quadTo(x + 48 * s, base - 250 * s, x + 12 * s, base); p.close()
    for ang in (-160, -120, -60, -20, -90):
        a = math.radians(ang)
        tipx, tipy = x + 18 * s + math.cos(a) * 190 * s, base - 480 * s + math.sin(a) * 110 * s + 60 * s
        q = skia.Path(); q.moveTo(x + 18 * s, base - 482 * s)
        q.quadTo((x + 18 * s + tipx) / 2, base - 560 * s, tipx, tipy)
        q.quadTo((x + 18 * s + tipx) / 2, base - 520 * s, x + 18 * s, base - 470 * s); q.close(); p.addPath(q)
    return p

def curtains(cv, t):
    sway = math.sin(t * 1.2) * 6
    for side in (-1, 1):
        p = skia.Path(); x0 = 0 if side < 0 else W
        p.moveTo(x0, 0); p.lineTo(x0 - side * -230, 0)
        p.cubicTo(x0 + side * -170 + sway, 500, x0 + side * -260, 900, x0 + side * -140 + sway, 1260)
        p.lineTo(x0, 1260); p.close()
        cut(cv, p, '#8e1d17', side * -10, 14, 0.4)
        for k in range(4):
            xx = x0 + side * -(40 + k * 45)
            cv.drawLine(xx, 0, xx + sway * 0.5, 1150 - k * 120, paint('#5e120e', 0.6, 'stroke', 5))
    top = skia.Path(); top.moveTo(0, 0); top.lineTo(W, 0); top.lineTo(W, 120)
    for k in range(6, -1, -1):
        x = k * W / 6
        if k < 6: top.quadTo(x + W / 12, 200, x, 120)
    top.lineTo(0, 120); top.close()
    cut(cv, top, '#a3241c', 0, 12, 0.4)

def chandelier(cv, x, y, t):
    cv.drawLine(x, 0, x, y, paint(SHADOW, 1, 'stroke', 5))
    p = skia.Path(); p.addOval(skia.Rect(x - 120, y, x + 120, y + 40))
    for k in range(5):
        cx = x - 100 + k * 50; p.addRect(skia.Rect(cx - 5, y - 40, cx + 5, y))
    cut(cv, p, SHADOW, 6, 10, 0.3)
    for k in range(5):
        cx = x - 100 + k * 50; fl = 0.8 + 0.2 * math.sin(t * 9 + k)
        cv.drawCircle(cx, y - 48, 9 * fl, paint(AMBER)); glow(cv, cx, y - 48, 60, '#ffb84a', 0.3 * fl)

def blueprint_card(cv, rot=2):
    cv.save(); cv.translate(W / 2, 720); cv.rotate(rot); cv.translate(-W / 2, -720)
    card = rect_path(80, 230, W - 80, 1180); cut(cv, card, BP, 14, 20, 0.5)
    cv.save(); cv.clipPath(card); glow(cv, W / 2, 700, 700, '#2f7fd0', 0.35)
    for x in range(80, W, 40):
        cv.drawLine(x, 230, x, 1180, paint('#ffffff', 0.10 if x % 200 else 0.2, 'stroke', 1.5))
    for y in range(230, 1180, 40):
        cv.drawLine(80, y, W - 80, y, paint('#ffffff', 0.10 if y % 200 else 0.2, 'stroke', 1.5))
    cv.restore(); cv.restore()

def label_card(cv, text, x, y, size=44, bg=RUST, fg=PAPER, rot=-3, fname='Mono-Bold', a=1.0, s=1.0):
    f = font(fname, size); w = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    cut(cv, rect_path(-w / 2 - 28, -size * 1.0, w / 2 + 28, size * 0.42), bg, 6, 9, 0.35 * a)
    text_c(cv, text, 0, 0, f, paint(fg, a)); cv.restore()

def stamp_at(cv, text, x, y, lt, size=130, color=RUST, rot=-10, bg=PAPER):
    st = clamp(lt / 0.28)
    if st <= 0: return
    s = 2.0 - 1.0 * ease_out(st); a = ease_out(st)
    f = font('Inter-Black', size); w = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    cut(cv, rect_path(-w / 2 - 36, -size * 0.92, w / 2 + 36, size * 0.33), bg, 10, 14, 0.5 * a)
    cv.drawRoundRect(skia.Rect(-w / 2 - 22, -size * 0.8, w / 2 + 22, size * 0.21), 10, 10, paint(color, a, 'stroke', 8))
    text_c(cv, text, 0, 0, f, paint(color, a)); cv.restore()

def mascot_draw(cv, x, y, s, a=1.0, color=SHADOW, sh=0.5):
    if a < 1: cv.saveLayerAlpha(None, int(255 * clamp(a)))
    cut(cv, man_path(x, y, s), color, 12 * s / 0.8, 16 * s / 0.8, sh)
    if a < 1: cv.restore()

def chip_stack(cv, x, base, n, color, w=130):
    if n <= 0: return
    cut(cv, rect_path(x - w / 2, base - n * 23, x + w / 2, base), color, 8, 12, 0.45)
    for k in range(n):
        y = base - k * 23
        cv.drawLine(x - w / 2, y, x + w / 2, y, paint('#000000', 0.35, 'stroke', 2))
        for j in range(4):
            sx = x - w / 2 + 18 + j * (w - 36) / 3
            cv.drawRect(skia.Rect(sx - 7, y - 19, sx + 7, y - 4), paint(PAPER, 0.85))

def chip_face(cv, x, y, r, color, rot=0, sx=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sx, 1)
    cut(cv, circ_path(0, 0, r), color, 6, 9, 0.45)
    for k in range(8):
        a = math.radians(k * 45)
        cv.drawLine(math.cos(a) * r * 0.78, math.sin(a) * r * 0.78, math.cos(a) * r * 0.98, math.sin(a) * r * 0.98, paint(PAPER, 1, 'stroke', 14))
    cv.drawCircle(0, 0, r * 0.55, paint(PAPER, 1, 'stroke', 4)); cv.restore()

def bill(cv, x, y, rot, sx=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sx, 1)
    cut(cv, rect_path(-170, -78, 170, 78), '#7fa36a', 6, 9, 0.4)
    cv.drawRect(skia.Rect(-155, -64, 155, 64), paint('#3f6b38', 1, 'stroke', 4))
    cv.drawCircle(0, 0, 44, paint('#5d8a52'))
    f = font('Inter-Black', 40)
    cv.drawString('100', -150, -20, f, paint('#2c4d27')); cv.drawString('100', 72, 50, f, paint('#2c4d27'))
    cv.restore()

def glass(cv, x, y, s, tilt=0):
    cv.save(); cv.translate(x, y); cv.rotate(tilt); cv.scale(s, s)
    bowl = skia.Path(); bowl.moveTo(-150, -260); bowl.lineTo(150, -260); bowl.lineTo(0, -40); bowl.close()
    stem = skia.Path(); stem.addRect(skia.Rect(-10, -45, 10, 160)); stem.addOval(skia.Rect(-110, 150, 110, 190))
    cut(cv, stem, '#e9e2d0', 8, 12, 0.45); cut(cv, bowl, '#e9e2d0', 8, 12, 0.45)
    liq = skia.Path(); liq.moveTo(-118, -213); liq.lineTo(118, -213); liq.lineTo(0, -48); liq.close()
    cv.drawPath(liq, paint('#d6463a')); cv.drawCircle(70, -250, 26, paint('#2f7a3a'))
    cv.drawLine(70, -250, 120, -330, paint(SHADOW, 1, 'stroke', 6)); cv.restore()

def hourglass(cv, x, y, s, sand):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    frame = skia.Path(); frame.addRect(skia.Rect(-170, -300, 170, -270)); frame.addRect(skia.Rect(-170, 270, 170, 300))
    frame.addRect(skia.Rect(-160, -270, -140, 270)); frame.addRect(skia.Rect(140, -270, 160, 270))
    cut(cv, frame, '#3a2418', 8, 12, 0.45)
    gl = skia.Path(); gl.moveTo(-120, -270); gl.lineTo(120, -270); gl.lineTo(14, 0); gl.lineTo(120, 270); gl.lineTo(-120, 270)
    gl.lineTo(-14, 0); gl.close(); cv.drawPath(gl, paint('#ffffff', 0.35))
    top = skia.Path(); h = 220 * (1 - sand)
    top.moveTo(-120 * h / 270 - 14, -h); top.lineTo(120 * h / 270 + 14, -h); top.lineTo(14, 0); top.lineTo(-14, 0); top.close()
    if sand < 1: cv.drawPath(top, paint(AMBER))
    bot = skia.Path(); hb = 220 * sand
    bot.moveTo(-120, 270); bot.lineTo(120, 270); bot.lineTo(120 - 40 * sand, 270 - hb); bot.lineTo(-120 + 40 * sand, 270 - hb); bot.close()
    cv.drawPath(bot, paint(AMBER))
    if sand < 1: cv.drawLine(0, 0, 0, 270 - hb, paint(AMBER, 1, 'stroke', 6))
    cv.drawPath(gl, paint(INKD, 1, 'stroke', 6)); cv.restore()

R1 = random.Random(7)
STARS = [(R1.uniform(0, W), R1.uniform(0, 900), R1.uniform(1.2, 3.2), R1.uniform(0, 6.28)) for _ in range(110)]

# ======================= element drawers =======================
# each: fn(cv, e, lt, R)   lt = seconds since the element started, R(name) = seconds since "<name>_at"
DRAW = {}
def drawer(name):
    def deco(fn): DRAW[name] = fn; return fn
    return deco

def fade_a(e, lt):
    """standard fade-in (0.3 s) used by labels and cards"""
    return ease_out(lt / e.get('fade', 0.3)) if lt < 9e5 else 1

@drawer('bg')
def d_bg(cv, e, lt, R):
    look = e.get('look', 'paper')
    if look == 'paper':
        paper_bg(cv)
        if e.get('glow'): glow(cv, W / 2, e.get('glow_y', 700), 600, '#ffcf6b', e['glow'])
    elif look == 'hall':
        paper_bg(cv, '#e9d9b6', '#cdb48a'); glow(cv, W / 2, 620, 560, '#ffd27a', 0.3)
        curtains(cv, lt); chandelier(cv, W / 2, 230, lt)
    elif look == 'dark':
        paper_bg(cv, '#2a1c12', '#0e0805'); glow(cv, W / 2, 760, 650, '#ffb84a', 0.28)
        if e.get('rays'):
            for k in range(18):
                a0 = math.radians(k * 20 + lt * 12); a1 = a0 + math.radians(8)
                p = skia.Path(); p.moveTo(W / 2, 760)
                p.lineTo(W / 2 + math.cos(a0) * 1500, 760 + math.sin(a0) * 1500)
                p.lineTo(W / 2 + math.cos(a1) * 1500, 760 + math.sin(a1) * 1500); p.close()
                cv.drawPath(p, paint(AMBER, 0.06))
    elif look == 'study':  # EP02 cards: dark brown desk
        paper_bg(cv, '#3a2a1c', '#160e08'); glow(cv, W / 2, 700, 700, '#ffb84a', 0.18)
    elif look == 'red':
        paper_bg(cv, '#b8382c', '#5a1510'); glow(cv, W / 2, 720, 600, '#ff8a5a', 0.25)
    elif look == 'candle':
        paper_bg(cv, '#3a2a1c', '#160e08'); glow(cv, 820, 380, 520, '#ffb84a', 0.35)
        cut(cv, rect_path(800, 400, 860, 640), PAPER, 6, 10, 0.4)
        fl = 1 + 0.08 * math.sin(lt * 13)
        f = skia.Path(); f.moveTo(830, 330 - 20 * fl); f.quadTo(860, 380, 830, 400); f.quadTo(800, 380, 830, 330 - 20 * fl)
        cv.drawPath(f, paint(AMBER)); glow(cv, 830, 370, 140, '#ffcf6b', 0.5)
    elif look == 'blueprint':
        paper_bg(cv); blueprint_card(cv, e.get('rot', 1.5))
    elif look == 'sunset':
        paper_bg(cv, '#f0c49a', '#c9764e')
        cut(cv, circ_path(W / 2 + 120 - lt * 10, 760, 230), '#e8743b', 5, 8, 0.25)
        hills = skia.Path(); hills.moveTo(-100, 1000)
        hills.cubicTo(200, 820, 500, 900, 700, 860); hills.cubicTo(900, 820, 1100, 900, 1300, 880)
        hills.lineTo(1300, 1300); hills.lineTo(-100, 1300); hills.close(); hills.offset(-lt * 10, 0)
        cut(cv, hills, '#9a5a3a', 6, 8, 0.25)
    elif look == 'night':  # EP01 opening: red sun, far city, casino, palms, parallax
        paper_bg(cv); cam = lt
        sx = W / 2 + 160 - cam * 8
        cut(cv, circ_path(sx, 620, 250), '#b3261e', 6, 8, 0.3)
        far = skia.Path(); far.moveTo(-100, 1000)
        for i in range(14):
            x = -100 + i * 100 - cam * 12; yy = 900 - (60 if i % 3 else 140) - (i % 2) * 30
            far.lineTo(x, yy); far.lineTo(x + 100, yy)
        far.lineTo(W + 200, 1000); far.lineTo(W + 200, 1300); far.lineTo(-100, 1300); far.close()
        cut(cv, far, '#7a5a3a', 6, 8, 0.25)
        cx = W / 2 - cam * 22
        cut(cv, casino_sil(cx, 1150, 0.95), '#6b4630', 10, 14, 0.4)
        casino_windows(cv, cx, 1150, 0.95, '#e8b04a', 0.9)
        cut(cv, rect_path(-50, 1140, W + 50, H), '#1a100b', 0, -8, 0.35)
        cut(cv, palm(70 - cam * 45, 1250, 1.25), '#0d0806', 12, 16, 0.45)
        cut(cv, palm(W - 130 - cam * 45, 1270, 1.1), '#0d0806', 12, 16, 0.45)

@drawer('ground')
def d_ground(cv, e, lt, R):
    cut(cv, rect_path(-50, e.get('y', 1255), W + 50, H), e.get('color', GROUND), 0, -10, 0.35)

@drawer('dim')
def d_dim(cv, e, lt, R):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', e.get('amount', 0.35) * ease_out(lt / 0.3)))

@drawer('mascot')
def d_mascot(cv, e, lt, R):
    x = e.get('x', W / 2) + e.get('drift', 0) * lt + e.get('walk', 0) * ease_out(lt / e.get('walk_dur', 1.4))
    y = e.get('y', 820)
    if e.get('rise'): y += e['rise'] * (1 - ease_out(lt / e.get('rise_dur', 0.8)))
    a = ease_out(lt / e['fade']) if e.get('fade') else 1.0
    mascot_draw(cv, x, y, e.get('s', 0.78), a, col(e.get('color', SHADOW)), e.get('sh', 0.5))

@drawer('label')
def d_label(cv, e, lt, R):
    a = fade_a(e, lt)
    s = 0.6 + 0.4 * back_out(clamp(lt / 0.45)) if e.get('pop') else 1.0
    if e.get('pop') == 'big': s = back_out(clamp(lt / 0.45))
    label_card(cv, e['text'], e.get('x', W / 2), e['y'], e.get('size', 44), col(e.get('bg', RUST)), col(e.get('fg', PAPER)),
               e.get('rot', -3), e.get('font', 'Mono-Bold'), a, s)

@drawer('text')
def d_text(cv, e, lt, R):
    a = fade_a(e, lt) * e.get('alpha', 1)
    text_c(cv, e['text'], e.get('x', W / 2), e['y'], font(e.get('font', 'Mono-Bold'), e.get('size', 34)), paint(col(e.get('color', PAPER)), a))

@drawer('stamp')
def d_stamp(cv, e, lt, R):
    stamp_at(cv, e['text'], e.get('x', W / 2), e['y'], lt, e.get('size', 130), col(e.get('color', RUST)), e.get('rot', -10))

@drawer('word')
def d_word(cv, e, lt, R):
    """big cut-out word card (1800s, LUCK, MATHS, TIME). Optional strike_at tears it away."""
    fn = e.get('font', 'Playfair-Black'); size = e.get('size', 190)
    f = font(fn, size); w = f.measureText(e['text'])
    pop = e.get('pop', 'fade')
    if pop == 'back': s = back_out(clamp(lt / e.get('pop_dur', 0.8)), e.get('pop_k', 1.7)); a = ease_out(lt / 0.7)
    elif pop == 'slam': m = clamp(lt / 0.4); s = back_out(m, 2.2); a = clamp(m * 2)
    else: s = 1.0; a = ease_out(lt / 0.5)
    if s <= 0: return
    torn = ease_out(R('strike') / 0.3) if 'strike_at' in e else 0
    if torn > 0:
        e_line = ease_out(R('strike') / 0.25)
    cv.save(); cv.translate(e.get('x', W / 2), e['y']); cv.rotate(e.get('rot', -3) - e.get('tear_rot', 8) * torn)
    cv.translate(0, e.get('tear_drop', 60) * torn); cv.scale(s, s)
    al = a * (1 - e.get('tear_fade', 0.65) * torn)
    cut(cv, rect_path(-w / 2 - 40, -size * 0.9, w / 2 + 40, size * 0.26), col(e.get('card', PAPER)), 10, 14, 0.45 * al)
    if e.get('glow'): glow(cv, 0, -size * 0.33, size * 1.8, '#e2b84a', 0.35 * a)
    text_c(cv, e['text'], 0, 0, f, paint(col(e.get('ink', INKD)), al))
    if torn > 0:
        cv.drawLine(-w / 2 - 30, -size * 0.32, -w / 2 - 30 + (w + 60) * e_line, -size * 0.36, paint(RUST, 1, 'stroke', size * 0.12))
    cv.restore()

@drawer('numcard')
def d_numcard(cv, e, lt, R):
    """countdown number card that flips in and wobbles"""
    n = e['n']; flip = clamp(lt / 0.35)
    sx = abs(math.cos((1 - ease_out(flip)) * math.pi)) if flip < 1 else 1
    s = 0.8 + 0.2 * back_out(flip)
    cv.save(); cv.translate(W / 2, 760); cv.rotate(-3 + 2 * math.sin(lt * 2)); cv.scale(sx * s, s)
    cut(cv, rect_path(-260, -360, 260, 360), RUST if n == 1 else PAPER, 14, 20, 0.55)
    cv.drawRect(skia.Rect(-230, -330, 230, 330), paint(PAPER if n == 1 else INKD, 0.9, 'stroke', 6))
    text_c(cv, str(n), 0, 150, font('Playfair-Black', 480), paint(PAPER if n == 1 else INKD))
    cv.restore()

@drawer('fan')
def d_fan(cv, e, lt, R):
    """countdown hook: numbered cards fan out, the last one is the red '?' card"""
    n_cards = e.get('n', 5)
    for i in range(n_cards):
        a = back_out(prog(lt, 0.15 + i * 0.12, 0.45 + i * 0.12), 1.8)
        if a <= 0: continue
        n = n_cards - i; ang = -30 + i * 15 * 5 / n_cards
        cv.save(); cv.translate(W / 2 + 60, 1320); cv.rotate(ang * a); cv.translate(0, -640); cv.scale(a, a)
        r = rect_path(-95, -140, 95, 140)
        if n == 1:
            cut(cv, r, RUST, 8, 12, 0.5); cv.drawRect(skia.Rect(-85, -130, 85, 130), paint(PAPER, 0.9, 'stroke', 5))
            text_c(cv, '?', 0, 50, font('Playfair-Black', 170), paint(PAPER))
        else:
            cut(cv, r, PAPER, 8, 12, 0.5); text_c(cv, str(n), 0, 55, font('Playfair-Black', 170), paint(INKD))
        cv.restore()

@drawer('table_wheel')
def d_table_wheel(cv, e, lt, R):
    """EP01 watcher scene: felt table, spinning wheel with ball, slow push-in"""
    tab = skia.Path(); tab.addOval(skia.Rect(60, 900, W - 60, 1260)); cut(cv, tab, GREEN, 8, 14, 0.45)
    zoom = 1 + 0.04 * lt
    cv.save(); cv.translate(W / 2, 700); cv.scale(zoom, zoom); cv.translate(-W / 2, -700)
    cv.drawCircle(W / 2 + 10, 718, 300 * 1.1, paint('#000000', 0.35, blur=14))
    wheel(cv, W / 2, 700, 270, rot=lt * 70)
    ba = math.radians(-lt * 260)
    cv.drawCircle(W / 2 + math.cos(ba) * 262, 700 + math.sin(ba) * 262, 12, paint('#ffffff'))
    cv.restore()

@drawer('nobet_eye')
def d_nobet_eye(cv, e, lt, R):
    """crossed-out chip ('no bet') that turns into an eye ('just watched') at eye_at"""
    x, y = e.get('x', 860), e.get('y', 1040)
    re = R('eye')
    a = ease_out(clamp((lt - 0.3) / 0.5)) * (1 - clamp((re + 0.15) / 0.3))
    if a > 0:
        cv.save(); cv.translate(x, y); cv.scale(0.6 + 0.4 * a, 0.6 + 0.4 * a)
        cut(cv, circ_path(0, 0, 70), RUST, 6, 9, 0.4 * a)
        cv.drawCircle(0, 0, 52, paint(PAPER, a, 'stroke', 7)); cv.drawLine(-85, -85, 85, 85, paint(PAPER, a, 'stroke', 14))
        cv.restore()
    b = ease_out(re / 0.45)
    if b > 0:
        cv.save(); cv.translate(x, y)
        p = skia.Path(); p.moveTo(-100, 0); p.quadTo(0, -80 * b, 100, 0); p.quadTo(0, 80 * b, -100, 0); p.close()
        cut(cv, p, PAPER, 6, 9, 0.4 * b)
        cv.drawCircle(0, 0, 34 * b, paint(INKD)); cv.drawCircle(10, -10, 9 * b, paint('#ffffff'))
        cv.restore()

NB_R = random.Random(3)
NB = [NB_R.randint(0, 36) for _ in range(120)]

@drawer('tally')
def d_tally(cv, e, lt, R):
    """EP01 notebook: numbers written down over 'dur' seconds with a pen, day counter on top"""
    dur = e.get('dur', 3.3); days = e.get('days', 30)
    cv.save(); cv.translate(W / 2, 760); cv.rotate(-4 + 1.2 * math.sin(lt * 0.7)); cv.translate(-W / 2, -760)
    cut(cv, rect_path(130, 300, W - 150, 1170), PAPER, 14, 20, 0.55)
    for k in range(16):
        y = 390 + k * 48; cv.drawLine(170, y, W - 190, y, paint('#9fb6c8', 0.5, 'stroke', 2))
    cv.drawLine(240, 300, 240, 1170, paint(RUST, 0.6, 'stroke', 3))
    fm = font('Mono-Bold', 34); shown = int(clamp(lt / dur) * 96)
    for i in range(min(shown, 96)):
        r, c = divmod(i, 6); x = 270 + c * 108; y = 380 + r * 48
        if y > 1150: break
        cv.drawString(f'{NB[i]:>2}', x, y, fm, paint(INKD, 0.4 + 0.6 * clamp((shown - i) / 4)))
    pr = min(shown, 95); r, c = divmod(pr, 6)
    px, py = 270 + c * 108 + 60, 380 + r * 48 - 10
    pen = skia.Path(); pen.moveTo(px, py); pen.lineTo(px + 26, py - 14); pen.lineTo(px + 230, py - 210)
    pen.lineTo(px + 214, py - 226); pen.lineTo(px + 12, py - 30); pen.close()
    cut(cv, pen, SHADOW, 10, 14, 0.45); cv.restore()
    day = 1 + int(clamp(lt / (dur * 1.09)) * (days - 1))
    label_card(cv, f'{e.get("unit", "DAY")} {day:02d} / {days}', W / 2, 250, 46, RUST, PAPER, rot=-2)

@drawer('balance')
def d_balance(cv, e, lt, R):
    """blueprint: turning gears (FIG. 1) become a wobbling wheel with an off-centre axis (FIG. 2) at wheel_at"""
    rw = R('wheel'); line = paint(BP_LINE, 0.95, 'stroke', 4)
    ga = 1 - clamp((rw + 0.15) / 0.35)
    if ga > 0:
        lp = paint(BP_LINE, ga, 'stroke', 4)
        cv.drawPath(gear_path(430, 640, 220, 14, lt * 40), lp)
        cv.drawPath(gear_path(430 + 340, 640 + 210, 140, 9, -lt * 40 * 14 / 9 + 10), lp)
        cv.drawPath(gear_path(300, 960, 100, 8, -lt * 40 * 14 / 8 + 5), lp)
        text_c(cv, e.get('fig1', 'FIG. 1  MACHINES'), W / 2, 330, font('Mono-Bold', 36), paint(BP_HI, ga))
    b = ease_out((rw + 0.05) / 0.55)
    if b > 0:
        wob = math.sin(lt * 9) * 14 * clamp((rw - 0.8) / 1.0)
        cx, cy, r = W / 2, 720, 300 * (0.75 + 0.25 * b)
        lp = paint(BP_LINE, b, 'stroke', 4)
        for rr in (r, r * 0.85, r * 0.55, r * 0.2): cv.drawCircle(cx + wob * (1 - rr / r), cy, rr, lp)
        rot = math.radians(lt * 90)
        for i in range(37):
            a = rot + i * 2 * math.pi / 37
            cv.drawLine(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55, cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85, paint(BP_LINE, 0.8 * b, 'stroke', 2))
        c = ease_out((rw - 0.8) / 0.6)
        if c > 0:
            cv.drawLine(cx, 330, cx, 1110, paint(BP_LINE, 0.5 * c, 'stroke', 2)); cv.drawCircle(cx, cy, 9, paint(BP_LINE, c))
            cv.drawCircle(cx + wob + 16, cy - 8, 12, paint(BP_HI, c))
            cv.drawLine(cx + wob + 16, cy - 8, cx + 290, cy - 330, paint(BP_HI, c, 'stroke', 3))
            cv.drawString(e.get('callout', 'AXIS OFF CENTRE?'), cx + 40, cy - 345, font('Mono-Bold', 32), paint(BP_HI, c))
            text_c(cv, e.get('fig2', 'FIG. 2  PERFECTLY BALANCED?'), W / 2, 1110, font('Mono-Bold', 34), paint(BP_HI, c))

@drawer('wheel_odds')
def d_wheel_odds(cv, e, lt, R):
    """EP01 'the flaw': lucky pockets glow, the wheel moves up and a frequency chart grows"""
    hot = set(e.get('hot', [7, 8, 9, 17, 18, 19, 22, 28, 29]))
    rng = random.Random(11); bars = [(n, 1.0 + (0.55 if n in hot else 0) + rng.uniform(-0.12, 0.12)) for n in range(37)]
    rb = R('bars')
    move = ease_in_out((rb + 0.4) / 0.8)
    Rr = 290 - 120 * move; cy = 690 - 330 * move
    hl = ease_in_out((lt - 0.25) / 0.85) * (0.75 + 0.25 * math.sin(lt * 6))
    cv.drawCircle(W / 2 + 12, cy + 18, Rr * 1.1, paint('#000000', 0.4, blur=14))
    wheel(cv, W / 2, cy, Rr, rot=lt * 20, highlight=hot, hl_amt=hl)
    g = ease_out(rb / 1.5)
    if g > 0:
        x0, base, bw, gap = 95, 1150, 20, 4.3
        for i, (n, v) in enumerate(bars):
            x = x0 + i * (bw + gap); h = 330 * v * ease_out((rb - i * 0.02) / 1.1)
            cut(cv, rect_path(x, base - h, x + bw, base), RUST if n in hot else BROWN, 4, 6, 0.35 * g)
        avg = base - 330
        cv.drawLine(x0 - 10, avg, W - 80, avg, paint(INKD, 0.8 * g, 'stroke', 3))
        cv.drawString(e.get('line', 'EXPECTED'), W - 270, avg - 14, font('Mono-Bold', 28), paint(INKD, g))
        label_card(cv, e.get('label', 'HOW OFTEN EACH NUMBER LANDED'), W / 2, 1215, 30, INKD, PAPER, rot=0, a=g)

HOT_DEFAULT = {7, 8, 9, 17, 18, 19, 22, 28, 29}

@drawer('streak')
def d_streak(cv, e, lt, R):
    """chips land on the lucky pockets, then a row of W tags (wins) pops in from streak_at"""
    hot = set(e.get('hot', HOT_DEFAULT))
    cv.drawCircle(W / 2 + 12, 578, 300, paint('#000000', 0.4, blur=14))
    wheel(cv, W / 2, 560, 270, rot=0, highlight=hot, hl_amt=0.75 + 0.25 * math.sin(lt * 6))
    step = 360 / 37
    for k, i in enumerate([i for i, n in enumerate(ORDER) if n in hot]):
        d = prog(lt, 0.05 + k * 0.1, 0.35 + k * 0.1)
        if d <= 0: continue
        am = math.radians(i * step - 90)
        tx, ty = W / 2 + math.cos(am) * 270 * 0.78, 560 + math.sin(am) * 270 * 0.78
        y = ty - 500 * (1 - ease_out(d)); sc = 1.6 - 0.6 * ease_out(d)
        cut(cv, circ_path(tx, y, 25 * sc), RUST, 4, 7, 0.45); cv.drawCircle(tx, y, 17 * sc, paint(PAPER, 1, 'stroke', 4 * sc))
    fw = font('Playfair-Black', 66); rs = R('streak')
    for k in range(e.get('wins', 9)):
        age = clamp((rs - k * 0.155) / 0.2)
        if age <= 0: continue
        sc = back_out(age, 2.5); x = W / 2 - 4 * 104 + k * 104
        cv.save(); cv.translate(x, 1010); cv.rotate(-4 + (k % 3) * 4); cv.scale(sc, sc)
        cut(cv, rect_path(-44, -50, 44, 46), PAPER, 5, 8, 0.4); text_c(cv, 'W', 0, 22, fw, paint(RUST)); cv.restore()

@drawer('counter')
def d_counter(cv, e, lt, R):
    """chip stacks grow while a big number counts up on a paper card (EP01 '2,000,000 FRANCS')"""
    glow(cv, W / 2, 700, 650, '#ffcf6b', 0.25 + 0.15 * clamp(lt / 8))
    if e.get('chips', True):
        for i, c in enumerate([RUST, INKD, BROWN, GREEN, RUST]):
            n = int(clamp((lt - i * 0.2) / 4.0) * 20)
            chip_stack(cv, W / 2 - 320 + i * 160, 1200, n, c)
    rc = R('count'); dur = e.get('dur', 3.0)
    a = ease_out((rc + 0.15) / 0.35)
    if a > 0:
        val = e['value'] * ease_in_out(rc / dur); dec = e.get('decimals', 0)
        s = f"{e.get('prefix', '')}{val:,.{dec}f}{e.get('suffix', '')}"
        full = f"{e.get('prefix', '')}{e['value']:,.{dec}f}{e.get('suffix', '')}"
        f = font('Playfair-Black', e.get('size', 150)); w = f.measureText(full)
        pop = 1 + (0.08 * math.exp(-(rc - dur) * 6) if rc > dur else 0)
        cv.save(); cv.translate(W / 2, 400); cv.rotate(-2); cv.scale(pop, pop)
        cut(cv, rect_path(-w / 2 - 40, -150, w / 2 + 40, 50), PAPER, 10, 14, 0.45 * a)
        text_c(cv, s, 0, 0, f, paint(INKD, a)); cv.restore()
        if e.get('unit'): label_card(cv, e['unit'], W / 2, 520, 46, RUST, PAPER, rot=-2, a=a)
    if e.get('after'):
        m = ease_out(R('after') / 0.5)
        if m > 0: label_card(cv, e['after'], W / 2, 640, 56, INKD, GOLD, rot=2, fname='Inter-Black', a=m, s=0.6 + 0.4 * back_out(m))

@drawer('patch')
def d_patch(cv, e, lt, R):
    """EP01 'the casino fought back': wheel, a wrench sweeps over it at fix_at, dividers flash"""
    rf = R('fix')
    flash = math.exp(-((rf - 0.7) ** 2) * 18) if rf > 0.1 else 0
    cv.drawCircle(W / 2 + 12, 738, 330 * 1.1, paint('#000000', 0.45, blur=16))
    wheel(cv, W / 2, 720, 300, rot=lt * 50, flash=flash)
    wa = ease_in_out(rf / 1.2)
    if 0 < wa < 1:
        cv.save(); cv.translate(W / 2, 720); cv.rotate(-60 + 120 * wa)
        wr = skia.Path(); wr.addRoundRect(skia.Rect(-14, -400, 14, -150), 10, 10); wr.addCircle(0, -420, 46)
        cut(cv, wr, '#d9d2c4', 6, 10, 0.45); cv.drawRect(skia.Rect(-14, -480, 14, -420), paint('#8e2a20')); cv.restore()

@drawer('town')
def d_town(cv, e, lt, R):
    pan = -45 * lt
    for i in range(7):
        x = -140 + i * 230 + pan; rise = ease_out(prog(lt, 0.08 * i, 0.08 * i + 0.5)); y = 1255 + 260 * (1 - rise)
        h = skia.Path(); h.addRect(skia.Rect(x, y - 360, x + 230, y))
        roof = skia.Path(); roof.moveTo(x - 10, y - 360); roof.lineTo(x + 115, y - 470); roof.lineTo(x + 240, y - 360); roof.close()
        h.addPath(roof); h.addRect(skia.Rect(x + 160, y - 470, x + 190, y - 400))
        cut(cv, h, '#3a2418' if i % 2 else '#2c1a12', 10, 14, 0.45)
        for wx, wy in ((40, -300), (140, -300), (40, -180)):
            r = skia.Rect(x + wx, y + wy, x + wx + 50, y + wy + 70); cv.drawRect(r, paint(AMBER)); glow(cv, r.centerX(), r.centerY(), 60, '#ffb84a', 0.25)
        for k in range(3):
            sy = y - 490 - ((lt * 60 + k * 50) % 150)
            cv.drawCircle(x + 175 + math.sin(lt * 2 + k) * 10, sy, 14 + k * 4, paint(PAPER, 0.35))

@drawer('wallclock')
def d_wallclock(cv, e, lt, R):
    """EP02: wall panel with the pale mark where a clock should hang, magnifier sweeping until stop_at"""
    cut(cv, rect_path(250, 380, W - 250, 1000), '#7a5236', 10, 14, 0.45)
    for k in range(5): cv.drawLine(250, 420 + k * 130, W - 250, 420 + k * 130, paint('#5e3d27', 0.6, 'stroke', 3))
    cx, cy = W / 2, 640
    cv.drawCircle(cx, cy, 150, paint('#8f6646'))
    dash = paint(PAPER, 0.8, 'stroke', 6); dash.setPathEffect(skia.DashPathEffect.Make([26, 18], lt * 30))
    cv.drawCircle(cx, cy, 150, dash); cv.drawCircle(cx, cy - 180, 9, paint(SHADOW))
    m = ease_out(prog(lt, 0.6, 1.0))
    if m > 0 and R('stop') < 0:
        ang = lt * 2.2; mx, my = cx + math.cos(ang) * 230, cy + math.sin(ang * 1.3) * 170
        cv.save(); cv.translate(mx, my); cv.saveLayerAlpha(None, int(255 * m))
        hnd = skia.Path(); hnd.addRoundRect(skia.Rect(55, 55, 85, 230), 14, 14)
        hm = skia.Matrix(); hm.setRotate(-35); hnd.transform(hm); cut(cv, hnd, SHADOW, 6, 10, 0.4)
        cv.drawCircle(0, 0, 95, paint('#ffffff', 0.18))
        ring = skia.Path(); ring.addCircle(0, 0, 95); ring.addCircle(0, 0, 78); ring.setFillType(skia.PathFillType.kEvenOdd)
        cut(cv, ring, SHADOW, 6, 10, 0.4); cv.restore(); cv.restore()

def card_frame(cv, y, lt, rot):
    a = ease_out(lt / 0.3)
    if a <= 0: return False
    cv.save(); cv.translate(W / 2 + (1 - a) * 900, y); cv.rotate(rot)
    cut(cv, rect_path(-400, -165, 400, 165), PAPER, 10, 14, 0.45); return True

def icon(cv, name, lt):
    """small illustrations on the left of a card (card-local coordinates, centre -230, 0)"""
    if name == 'clock':
        cv.drawCircle(-230, 0, 110, paint('#ffffff')); cv.drawCircle(-230, 0, 110, paint(INKD, 1, 'stroke', 10))
        hand = lt * 4
        cv.drawLine(-230, 0, -230 + math.cos(hand) * 80, math.sin(hand) * 80, paint(INKD, 1, 'stroke', 9))
        cv.drawLine(-230, 0, -230, -60, paint(INKD, 1, 'stroke', 9))
        x = ease_out((lt - 0.35) / 0.25)
        if x > 0:
            cv.drawLine(-340, -110, -340 + 220 * x, -110 + 220 * x, paint(RUST, 1, 'stroke', 18))
            cv.drawLine(-120, -110, -120 - 220 * x, -110 + 220 * x, paint(RUST, 1, 'stroke', 18))
    elif name == 'window':
        wr = skia.Rect(-330, -120, -130, 120); cv.drawRect(wr, paint('#9ec6e0')); cv.drawCircle(-230, -20, 40, paint('#ffd36b'))
        b = clamp((lt - 0.15) / 0.8); rows = int(b * 8 + 0.999) if b > 0 else 0
        for rr in range(rows):
            y = 120 - (rr + 1) * 30; off = 0 if rr % 2 else 25
            for cc in range(-1, 5):
                bx = -330 + off + cc * 50; br = skia.Rect(max(bx, -330), y, min(bx + 48, -130), y + 28)
                if br.width() > 0: cv.drawRect(br, paint('#9b4a32'))
        cv.drawRect(wr, paint(INKD, 1, 'stroke', 8))
    elif name == 'sunset':
        sky = skia.Rect(-370, -135, -110, 135); d = ease_in_out((lt - 0.25) / 1.6)
        sp = skia.Paint()
        sp.setShader(skia.GradientShader.MakeLinear([(0, -135), (0, 135)], [C('#f0a060') if d < 0.5 else C('#1b2a45'), C('#e8743b') if d < 0.5 else C('#0b1222')]))
        cv.drawRect(sky, sp); cv.save(); cv.clipRect(sky)
        cv.drawCircle(-240, -30 + 220 * d, 60, paint('#ffd36b', 1 - 0.6 * d)); cv.drawRect(skia.Rect(-370, 70, -110, 135), paint('#2a1c12'))
        cv.restore(); cv.drawRect(sky, paint(INKD, 1, 'stroke', 8))
    elif name == 'chip':
        chip_face(cv, -230, 0, 105, RUST, lt * 40)
    elif name == 'cash':
        cv.save(); cv.translate(-230, 0); cv.scale(0.62, 0.62); bill(cv, 0, 0, -6); cv.restore()
    elif name == 'wheel':
        wheel(cv, -230, 0, 105, lt * 40)
    elif name == 'drink':
        glass(cv, -230, 60, 0.55)
    elif name == 'dice':
        for dx, rot in ((-280, -10), (-175, 12)):
            cv.save(); cv.translate(dx, 0); cv.rotate(rot)
            cut(cv, rect_path(-55, -55, 55, 55), PAPER, 5, 8, 0.45); cv.drawRoundRect(skia.Rect(-55, -55, 55, 55), 12, 12, paint(INKD, 1, 'stroke', 6))
            for px, py in ((-25, -25), (0, 0), (25, 25)): cv.drawCircle(px, py, 9, paint(RUST))
            cv.restore()

CARD_SLOTS = [(330, -2), (700, 2), (1070, -1.5)]

@drawer('cards')
def d_cards(cv, e, lt, R):
    """up to 3 paper cards that slide in from the right, each with an icon and a short line (EP02)"""
    f = font('Inter-Black', 54)
    for i, it in enumerate(e['items'][:3]):
        li = R(f'item{i}')
        y, rot = CARD_SLOTS[i]
        if card_frame(cv, y, li, rot):
            icon(cv, it.get('icon', 'chip'), li)
            cv.drawString(it['text'], -70, 20, f, paint(INKD)); cv.restore()

@drawer('book')
def d_book(cv, e, lt, R):
    """EP02: a book with a gold title opens at open_at"""
    op = ease_in_out(R('open') / 0.8)
    cv.save(); cv.translate(W / 2 - 40, 830); cv.rotate(-4); bw, bh = 520, 660
    cut(cv, rect_path(-bw / 2, -bh / 2, bw / 2, bh / 2), '#1d3b2c', 14, 20, 0.5)
    cv.drawPath(rect_path(-bw / 2 + 16, -bh / 2 + 14, bw / 2 - 10, bh / 2 - 12), paint(PAPER))
    for k in range(14):
        cv.drawLine(-bw / 2 + 60, -bh / 2 + 90 + k * 38, bw / 2 - 60 - (90 if k % 5 == 4 else 0), -bh / 2 + 90 + k * 38, paint('#6b5a44', 0.55 * op, 'stroke', 7))
    sx = math.cos(op * math.pi)
    cv.save(); cv.translate(-bw / 2, 0); cv.scale(sx, 1)
    cv.drawPath(rect_path(0, -bh / 2, bw, bh / 2), paint('#24503a' if sx > 0 else '#183526'))
    if sx > 0.15:
        cv.drawRect(skia.Rect(30, -bh / 2 + 30, bw - 30, bh / 2 - 30), paint(AMBER, 0.9, 'stroke', 5))
        fb = font('Playfair-Black', 70)
        lines = e.get('title', ['DESIGNING', 'CASINOS'])
        for k, ln in enumerate(lines[:2]): text_c(cv, ln, bw / 2, -60 + 90 * k, fb, paint(AMBER))
        cv.drawLine(bw / 2 - 90, 80, bw / 2 + 90, 80, paint(AMBER, 1, 'stroke', 4))
        cv.drawCircle(bw / 2, 170, 46, paint(AMBER, 0.9, 'stroke', 5)); cv.drawLine(bw / 2 - 30, 170, bw / 2 + 30, 170, paint(AMBER, 0.9, 'stroke', 5))
    cv.restore(); cv.restore()

MAZE = [(0, 0, 8, 0), (0, 8, 8, 8), (0, 0, 0, 7), (8, 1, 8, 8), (1, 1, 5, 1), (6, 0, 6, 2), (1, 1, 1, 4), (2, 2, 7, 2),
        (7, 2, 7, 6), (2, 2, 2, 6), (3, 3, 6, 3), (3, 3, 3, 7), (4, 4, 6, 4), (6, 4, 6, 7), (1, 5, 1, 8), (4, 5, 4, 8),
        (5, 5, 5, 7), (2, 7, 3, 7), (7, 7, 8, 7), (0, 7, 1, 7)]
SPOTS = [(1.5, 0.5), (3.5, 0.5), (2.5, 1.5), (4.5, 2.5), (6.5, 3.5), (2.5, 3.5), (5.5, 5.5), (3.5, 5.5), (0.5, 2.5),
         (6.5, 6.5), (2.5, 6.5), (7.5, 4.5)]
LOOP = [(0.5, 7.5), (0.5, 4.5), (1.5, 4.5), (1.5, 1.5), (5.5, 1.5), (5.5, 0.5), (7.5, 0.5), (7.5, 1.5), (6.5, 1.5),
        (6.5, 3.5), (3.5, 3.5), (3.5, 6.5), (2.5, 6.5), (2.5, 4.5), (1.5, 4.5), (0.5, 4.5)]

@drawer('maze')
def d_maze(cv, e, lt, R):
    """EP02 countdown: blueprint maze, a visitor going in circles, EXIT sign at exit_at, machines at machines_at"""
    ox, oy, cs = 180, 440, 90
    m = ease_out(lt / 0.3); lp = paint(BP_LINE, m, 'stroke', 6); drawn = clamp(lt / 0.8)
    for i, (x1, y1, x2, y2) in enumerate(MAZE):
        k = clamp(drawn * len(MAZE) - i)
        if k <= 0: continue
        cv.drawLine(ox + x1 * cs, oy + y1 * cs, ox + (x1 + (x2 - x1) * k) * cs, oy + (y1 + (y2 - y1) * k) * cs, lp)
    re, rm = R('exit'), R('machines')
    ex = ease_out((re + 0.1) / 0.3)
    if ex > 0:
        fl = 0.55 + 0.45 * (math.sin(lt * 17) > -0.3)
        cv.drawRoundRect(skia.Rect(ox + 8 * cs - 120, oy + 8 * cs + 18, ox + 8 * cs, oy + 8 * cs + 66), 8, 8, paint('#ff8f80', ex * fl))
        cv.drawString('EXIT', ox + 8 * cs - 104, oy + 8 * cs + 57, font('Inter-Black', 40), paint(BP, ex))
    w = (max(0, lt - 0.5) * 2.6) % (len(LOOP) - 1); i = int(w); f = w - i
    x = LOOP[i][0] + (LOOP[i + 1][0] - LOOP[i][0]) * f; y = LOOP[i][1] + (LOOP[i + 1][1] - LOOP[i][1]) * f
    cv.drawCircle(ox + x * cs, oy + y * cs, 18, paint(BP_HI, m))
    mc = clamp((rm + 0.1) / 1.0)
    for j, (sx, sy) in enumerate(SPOTS):
        q = back_out(clamp(mc * len(SPOTS) - j), 2.5)
        if q <= 0: continue
        cv.save(); cv.translate(ox + sx * cs, oy + sy * cs); cv.scale(q, q)
        cv.drawRoundRect(skia.Rect(-26, -32, 26, 32), 8, 8, paint(BP_HI))
        for kk in range(3): cv.drawRect(skia.Rect(-20 + kk * 14, -16, -10 + kk * 14, 4), paint(BP))
        cv.restore()
    hd = e.get('headers', ['THE MAZE', 'WHERE IS THE EXIT?', 'MACHINES EVERYWHERE'])
    hdr = hd[2] if rm > -0.1 else (hd[1] if re > -0.1 else hd[0])
    text_c(cv, hdr, W / 2, 380, font('Mono-Bold', 44), paint(BP_HI, m))

BILLS = [(W / 2 - 230, 560, -12), (W / 2 + 200, 520, 9), (W / 2 - 40, 760, 4), (W / 2 + 250, 860, -7), (W / 2 - 260, 920, 14), (W / 2 + 20, 1050, -4)]
CHIPC = [RUST, INKD, GREEN, '#1d5fa8', RUST, BROWN]

@drawer('cash_chips')
def d_cash_chips(cv, e, lt, R):
    """EP02: bills drop in, then flip into chips at flip_at"""
    rf = R('flip')
    for i, (x, y, r) in enumerate(BILLS):
        drop = ease_out(prog(lt, 0.05 * i, 0.05 * i + 0.4))
        if drop <= 0: continue
        yy = y - 700 * (1 - drop); fl = clamp((rf - i * 0.12) / 0.35)
        if fl < 0.5: bill(cv, x, yy, r, math.cos(fl * math.pi))
        else: chip_face(cv, x, yy, 95, CHIPC[i], r, -math.cos(fl * math.pi))

@drawer('drink')
def d_drink(cv, e, lt, R):
    """EP02: free drink with a swinging price tag; strike_at crosses the front, flip_at shows the back, woozy_at sways"""
    sway = ease_in_out(R('woozy') / 1.3) if 'woozy_at' in e else 0
    wob = math.sin(lt * 3.0) * 7 * sway
    cv.save(); cv.translate(W / 2, 700); cv.rotate(wob); cv.translate(-W / 2, -700)
    cut(cv, rect_path(-40, 1080, W + 40, 1260), '#4a2c1a', 0, -10, 0.4)
    glass(cv, W / 2 - 60, 900, 1.15, tilt=-4 + 6 * sway)
    sw = math.sin(lt * 4) * 10 * math.exp(-lt * 0.5) if lt < 1.6 else math.sin(lt * 4) * 5 * math.exp(-(lt - 1.6) * 0.6)
    fl = clamp(R('flip') / 0.3)
    cv.save(); cv.translate(W / 2 + 10, 640); cv.rotate(sw)
    cv.drawLine(0, 0, 40, 120, paint(SHADOW, 1, 'stroke', 4))
    cv.translate(40, 120); cv.rotate(-8); cv.scale(abs(math.cos(fl * math.pi)) if fl < 1 else 1, 1)
    tag = skia.Path(); tag.moveTo(0, 0); tag.lineTo(60, -40); tag.lineTo(440, -40); tag.lineTo(440, 120); tag.lineTo(60, 120); tag.close()
    cut(cv, tag, PAPER, 8, 12, 0.45); cv.drawCircle(40, 40, 10, paint(SHADOW))
    if fl < 0.5:
        cv.drawString(e.get('front', 'FREE'), 105, 75, font('Inter-Black', 96), paint(GREEN))
        x = ease_out(R('strike') / 0.2) if 'strike_at' in e else 0
        if x > 0: cv.drawLine(95, 50, 95 + 270 * x, 20, paint(RUST, 1, 'stroke', 16))
    else:
        back = e.get('back', ['PAID BY', 'YOUR BETS'])
        cv.drawString(back[0], 100, 30, font('Inter-Black', 46), paint(RUST))
        if len(back) > 1: cv.drawString(back[1], 100, 95, font('Inter-Black', 46), paint(RUST))
    cv.restore(); cv.restore()
    if sway > 0:
        for k in range(3):
            rr = 60 + ((lt * 70 + k * 50) % 150)
            cv.drawCircle(W / 2 - 60, 560, rr, paint(PAPER, 0.5 * sway * (1 - rr / 210), 'stroke', 5))

@drawer('puppet')
def d_puppet(cv, e, lt, R):
    """EP02: a giant hand works the gambler on strings"""
    d = ease_out(lt / 0.5); hy = 200 - 220 * (1 - d)
    hand = skia.Path(); hand.addRoundRect(skia.Rect(W / 2 - 230, hy - 220, W / 2 + 230, hy + 40), 60, 60)
    for k in range(4):
        fx = W / 2 - 190 + k * 125; hand.addRoundRect(skia.Rect(fx, hy + 10, fx + 85, hy + 120 + (k % 2) * 25), 40, 40)
    cut(cv, hand, SHADOW, 10, 16, 0.5)
    bob = math.sin(lt * 3) * 18; gx, gy = W / 2, 760 + bob
    tips = [(W / 2 - 150, hy + 120), (W / 2 - 25, hy + 145), (W / 2 + 100, hy + 120), (W / 2 + 225, hy + 145)]
    ends = [(gx - 150, gy + 170), (gx - 60, gy - 120), (gx + 60, gy - 120), (gx + 150, gy + 170)]
    s = ease_out((lt - 0.3) / 0.5)
    for (x1, y1), (x2, y2) in zip(tips, ends):
        cv.drawLine(x1, y1, x1 + (x2 - x1) * s, y1 + (y2 - y1) * s, paint(PAPER, 0.85, 'stroke', 3))
    mascot_draw(cv, gx, gy - 60, 0.78); chip_face(cv, gx + 200, gy + 260, 50, RUST, lt * 120)

@drawer('chart')
def d_chart(cv, e, lt, R):
    """EP02: blueprint chart, your money drifts down over time while the house line climbs"""
    ox, oy, cw, ch = 200, 1030, 700, 560
    a = ease_out(lt / 0.3); ax = paint(BP_LINE, a, 'stroke', 5)
    cv.drawLine(ox, oy, ox + cw, oy, ax); cv.drawLine(ox, oy, ox, oy - ch, ax)
    lf = font('Mono-Bold', 32)
    cv.drawString(e.get('x_label', 'TIME'), ox + cw - 80, oy + 50, lf, paint(BP_LINE, a))
    cv.save(); cv.translate(ox - 30, oy - ch / 2 + 170); cv.rotate(-90); cv.drawString(e.get('y_label', 'YOUR MONEY'), 0, 0, lf, paint(BP_LINE, a)); cv.restore()
    rng = random.Random(4); pts, v = [], 0.62
    for i in range(61): pts.append(v); v += rng.uniform(-0.05, 0.05) - 0.0085
    k = prog(lt, 0.3, 2.6); n = max(2, int(k * 60) + 1); pth = skia.Path()
    for i in range(n):
        x = ox + cw * i / 60; y = oy - ch * max(0.03, pts[i]); pth.moveTo(x, y) if i == 0 else pth.lineTo(x, y)
    cv.drawPath(pth, paint(BP_HI, a, 'stroke', 7))
    cv.drawCircle(ox + cw * (n - 1) / 60, oy - ch * max(0.03, pts[n - 1]), 14, paint(BP_HI, a))
    hs = skia.Path(); hs.moveTo(ox, oy - ch * 0.05); hs.lineTo(ox + cw * k, oy - ch * (0.05 + 0.85 * k))
    hp = paint('#ff8f80', a, 'stroke', 5); hp.setPathEffect(skia.DashPathEffect.Make([22, 14], 0)); cv.drawPath(hs, hp)
    if k > 0.6: cv.drawString(e.get('house', 'HOUSE'), ox + cw * k - 170, oy - ch * (0.05 + 0.85 * k) - 20, lf, paint('#ff8f80', ease_out((k - 0.6) * 4)))
    text_c(cv, e.get('title', 'THE LONGER YOU STAY'), W / 2, 360, font('Mono-Bold', 44), paint(BP_HI, a))

SYMS = ['7', 'BAR', 'STAR', 'BELL']
def reel_symbol(cv, sym, x, y, sc=1.0):
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    if sym == '7': text_c(cv, '7', 0, 45, font('Playfair-Black', 130), paint(RUST))
    elif sym == 'BAR':
        cv.drawRoundRect(skia.Rect(-62, -28, 62, 28), 8, 8, paint(INKD)); text_c(cv, 'BAR', 0, 16, font('Inter-Black', 40), paint(PAPER))
    elif sym == 'STAR':
        p = skia.Path()
        for k in range(10):
            r = 60 if k % 2 == 0 else 26; a = math.radians(-90 + k * 36)
            (p.moveTo if k == 0 else p.lineTo)(math.cos(a) * r, math.sin(a) * r)
        p.close(); cv.drawPath(p, paint(AMBER))
    else:
        p = skia.Path(); p.moveTo(-45, 35); p.quadTo(-45, -55, 0, -55); p.quadTo(45, -55, 45, 35); p.close()
        cv.drawPath(p, paint(AMBER)); cv.drawCircle(0, 45, 12, paint(AMBER))
    cv.restore()

CONF = [(random.Random(i).uniform(-1, 1), random.Random(i + 99).uniform(0.4, 1.0), i) for i in range(60)]

@drawer('slot')
def d_slot(cv, e, lt, R):
    """EP02 countdown #1: bet, reels stop at spin_at, machine celebrates at party_at, truth at lost_at, mask at mask_at"""
    rs, rp, rl, rk = R('spin'), R('party'), R('lost'), R('mask')
    lost = clamp((rl + 0.05) / 0.3)
    paper_bg(cv, '#3a1414' if lost > 0.5 else '#2a1c12', '#0e0805')
    party = clamp((rp + 0.1) / 0.3) * (1 - lost)
    glow(cv, W / 2, 640, 700, GOLD if lost < 0.5 else '#ff5a4a', 0.25 + 0.25 * party)
    cab = skia.Path(); cab.addRoundRect(skia.Rect(200, 270, W - 200, 1120), 60, 60); cut(cv, cab, '#7a1f19', 14, 20, 0.55)
    cv.drawRoundRect(skia.Rect(230, 300, W - 230, 1090), 46, 46, paint(AMBER, 0.85, 'stroke', 6))
    for k in range(13):
        bx = 270 + k * (W - 540) / 12; on = party > 0 and (int(lt * 10) + k) % 2 == 0
        cv.drawCircle(bx, 340, 14, paint('#fff1b0' if on else '#6b3a1a'))
        if on: glow(cv, bx, 340, 50, '#ffdf6b', 0.5 * party)
    wb = back_out(clamp((rp + 0.05) / 0.35), 2.2) * (1 - lost)
    if wb > 0:
        cv.save(); cv.translate(W / 2, 450); cv.rotate(-3 + math.sin(lt * 9) * 2 * party); cv.scale(wb, wb)
        f = font('Inter-Black', 110); bt = e.get('banner', 'WINNER!'); w = f.measureText(bt)
        cut(cv, rect_path(-w / 2 - 30, -100, w / 2 + 30, 30), GOLD, 8, 12, 0.5); text_c(cv, bt, 0, 0, f, paint(INKD)); cv.restore()
    win = skia.Rect(270, 520, W - 270, 780); cv.drawRect(win, paint(PAPER))
    final = e.get('reels', ['7', '7', 'BAR'])
    cv.save(); cv.clipRect(win); rw = win.width() / 3
    for r in range(3):
        cx = win.left() + rw * (r + 0.5); stop = rs - r * 0.25
        if lt > 0.2 and stop < 0:
            off = (lt * 9 + r) % 1.0
            for k in range(-1, 3): reel_symbol(cv, SYMS[(int(lt * 9) + k + r) % 4], cx, 650 + (k - off) * 170, 0.9)
        else:
            reel_symbol(cv, final[r] if stop >= 0 else SYMS[r], cx, 650)
        if r: cv.drawLine(win.left() + rw * r, 520, win.left() + rw * r, 780, paint(INKD, 0.4, 'stroke', 3))
    cv.restore(); cv.drawRect(win, paint(INKD, 1, 'stroke', 8))
    cv.drawRoundRect(skia.Rect(W / 2 - 60, 840, W / 2 + 60, 858), 8, 8, paint(SHADOW))
    cd = prog(lt, 0.05, 0.45)
    if 0 < cd < 1:
        cy = 700 + 150 * ease_in_out(cd)
        cv.drawCircle(W / 2, cy - 120, 40, paint(AMBER)); cv.drawCircle(W / 2, cy - 120, 30, paint('#c9922a', 1, 'stroke', 4))
    cut(cv, rect_path(300, 900, W - 300, 1080), PAPER, 8, 12, 0.5)
    lf = font('Mono-Bold', 44)
    cv.drawString(e.get('bet_label', 'BET'), 340, 960, lf, paint(INKD)); cv.drawString(e.get('bet', '$1.00'), W - 480, 960, lf, paint(INKD))
    if rs - 0.5 >= 0:
        cv.drawString(e.get('won_label', 'WON'), 340, 1030, lf, paint(GREEN)); cv.drawString(e.get('won', '$0.50'), W - 480, 1030, lf, paint(GREEN))
    if party > 0:
        for k in range(6):
            ph = (lt * 0.6 + k / 6) % 1; nx = 160 + (k % 3) * 380 + math.sin(lt * 3 + k) * 30; ny = 1100 - ph * 900
            cv.save(); cv.translate(nx, ny); cv.drawCircle(0, 0, 18, paint(PAPER, party * (1 - ph)))
            cv.drawLine(16, 0, 16, -70, paint(PAPER, party * (1 - ph), 'stroke', 6)); cv.restore()
        for dx, sp, i in CONF:
            ph = (rp * sp * 0.7 + i * 0.017) % 1
            cv.drawRect(skia.Rect(W / 2 + dx * 520, 200 + ph * 1000, W / 2 + dx * 520 + 14, 200 + ph * 1000 + 22), paint([RUST, AMBER, PAPER, GREEN][i % 4], party))
    if lost > 0:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', 0.35 * lost))
        stamp_at(cv, e.get('loss', '-$0.50'), W / 2, 700, rl - 0.15, 170, RUST, -8)
    mk = clamp((rk + 0.05) / 0.35)
    if mk > 0:
        a = ease_out(mk)
        cv.save(); cv.translate(W / 2, 560 - 120 * (1 - a)); cv.scale(a, a)
        p = skia.Path()
        p.moveTo(-330, -20); p.cubicTo(-300, -110, -120, -90, 0, -30); p.cubicTo(120, -90, 300, -110, 330, -20)
        p.cubicTo(300, 90, 120, 90, 0, 30); p.cubicTo(-120, 90, -300, 90, -330, -20); p.close()
        p.addOval(skia.Rect(-230, -40, -90, 30)); p.addOval(skia.Rect(90, -40, 230, 30)); p.setFillType(skia.PathFillType.kEvenOdd)
        cut(cv, p, AMBER, 10, 14, 0.55); cv.restore()
        if e.get('mask_label'):
            label_card(cv, e['mask_label'], W / 2, 1220, 50, GOLD, INKD, rot=-2, fname='Inter-Black', a=a)

@drawer('hourglass')
def d_hourglass(cv, e, lt, R):
    hourglass(cv, e.get('x', W / 2), e.get('y', 900), e.get('s', 0.88), clamp(lt / e.get('dur', 3.3)))

@drawer('outro')
def d_outro(cv, e, lt, R):
    """end card held after the last line: gambler, channel name, follow line"""
    o = ease_in_out(lt / 0.55)
    if o <= 0: return
    if o >= 1:
        paper_bg(cv, '#2a1c12', '#0e0805')
    else:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#120a06', o))
    glow(cv, W / 2, 640, 600, '#ffb84a', 0.25 * o)
    s = 0.9 + 0.1 * ease_out(o)
    cv.save(); cv.translate(W / 2, 700); cv.scale(s, s)
    mascot_draw(cv, 0, -420, 0.6, o, '#000000')
    fb = font('Playfair-Black', 120)
    text_c(cv, 'THE RIGGED', 0, 230, fb, paint(PAPER, o)); text_c(cv, 'GAME', 0, 360, fb, paint(GOLD, o))
    cv.restore()
    b = ease_out((lt - 0.45) / 0.4)
    if b > 0: label_card(cv, e.get('follow', 'FOLLOW FOR MORE CASINO SECRETS'), W / 2, 1290, 40, RUST, PAPER, rot=-2, a=b)

# ======================= text extents for the layout check =======================
def texts(e):
    """(text, font, size, centre_x, baseline_y, padding, max_width) for every text an element draws"""
    t = e['type']; out = []
    if t == 'label': out.append((e['text'], e.get('font', 'Mono-Bold'), e.get('size', 44), e.get('x', W / 2), e['y'], 56, 1000))
    elif t == 'text': out.append((e['text'], e.get('font', 'Mono-Bold'), e.get('size', 34), e.get('x', W / 2), e['y'], 0, 1000))
    elif t == 'stamp': out.append((e['text'], 'Inter-Black', e.get('size', 130), e.get('x', W / 2), e['y'], 72, 980))
    elif t == 'word': out.append((e['text'], e.get('font', 'Playfair-Black'), e.get('size', 190), e.get('x', W / 2), e['y'], 80, 1000))
    elif t == 'cards':
        for it in e['items']: out.append((it['text'], 'Inter-Black', 54, W / 2 + 120, 0, 0, 440))
    elif t == 'counter':
        full = f"{e.get('prefix', '')}{e['value']:,.{e.get('decimals', 0)}f}{e.get('suffix', '')}"
        out.append((full, 'Playfair-Black', e.get('size', 150), W / 2, 400, 80, 1000))
        if e.get('unit'): out.append((e['unit'], 'Mono-Bold', 46, W / 2, 520, 56, 1000))
        if e.get('after'): out.append((e['after'], 'Inter-Black', 56, W / 2, 640, 56, 1000))
    elif t == 'maze':
        for h in e.get('headers', []): out.append((h, 'Mono-Bold', 44, W / 2, 380, 0, 860))
    elif t == 'drink':
        out.append((e.get('front', 'FREE'), 'Inter-Black', 96, W / 2, 0, 0, 300))
        for b in e.get('back', []): out.append((b, 'Inter-Black', 46, W / 2, 0, 0, 320))
    elif t == 'book':
        for ln in e.get('title', []): out.append((ln, 'Playfair-Black', 70, W / 2, 0, 0, 440))
    elif t == 'chart':
        out.append((e.get('title', ''), 'Mono-Bold', 44, W / 2, 360, 0, 860))
    elif t == 'slot':
        out.append((e.get('banner', 'WINNER!'), 'Inter-Black', 110, W / 2, 450, 60, 680))
        out.append((e.get('loss', '-$0.50'), 'Inter-Black', 170, W / 2, 700, 72, 1000))
        for k in ('bet', 'won'): out.append((e.get(k, ''), 'Mono-Bold', 44, W / 2, 0, 0, 220))
        if e.get('mask_label'): out.append((e['mask_label'], 'Inter-Black', 50, W / 2, 1220, 56, 1000))
    elif t == 'balance':
        out.append((e.get('fig2', ''), 'Mono-Bold', 34, W / 2, 1110, 0, 860))
        out.append((e.get('callout', ''), 'Mono-Bold', 32, W / 2 + 40 + 200, 0, 0, 400))
    elif t == 'wheel_odds':
        out.append((e.get('label', ''), 'Mono-Bold', 30, W / 2, 1215, 56, 1000))
    elif t == 'tally':
        out.append((f'{e.get("unit", "DAY")} 00 / {e.get("days", 30)}', 'Mono-Bold', 46, W / 2, 250, 56, 1000))
    elif t == 'outro':
        out.append((e.get('follow', 'FOLLOW FOR MORE CASINO SECRETS'), 'Mono-Bold', 40, W / 2, 1290, 56, 1000))
    return out

# ======================= timeline, captions, frames =======================
class Timeline:
    def __init__(self, spec, times, words, total):
        self.spec, self.times, self.words, self.total = spec, times, words, total
        self.voice_end = times[-1][1]
        self.dur = self.voice_end + spec.get('hold', 2.6)
        self.scenes = []
        for k, sc in enumerate(spec['scenes']):
            st = 0.0 if k == 0 else self.tm(sc['start'])
            self.scenes.append({'start': st, 'els': sc['els']})
        for i, sc in enumerate(self.scenes):
            sc['end'] = self.scenes[i + 1]['start'] if i + 1 < len(self.scenes) else self.dur + 1
            for e in sc['els']: self.resolve(e)
        self.chunks = self.make_chunks()
        kw = set(w.lower().strip(".,!?'\"") for w in spec.get('caption_keywords', []))
        self.kw = kw

    def tm(self, v, default_delay=0.0):
        """beat reference -> seconds"""
        if v is None: return -100.0
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if v < 0: return -100.0
            return self.times[int(v)][0] - 0.1
        if v == 'end': return self.voice_end
        if isinstance(v, list):
            return (self.voice_end if v[0] == 'end' else self.times[int(v[0])][0] - 0.1) + v[1]
        if isinstance(v, dict):
            b = int(v['b']); base = self.times[b][0] - 0.1
            if 'w' in v: base = self.words[b][min(int(v['w']), len(self.words[b]) - 1)][1] - 0.05
            return base + v.get('d', 0)
        raise ValueError(f'bad time reference {v!r}')

    def resolve(self, e):
        e['_t0'] = self.tm(e.get('at', -1)) + e.get('delay', 0) if e.get('at', -1) != -1 else -100.0
        e['_until'] = self.tm(e['until']) if 'until' in e else None
        for k, v in list(e.items()):
            if k.endswith('_at') and not k.startswith('_'): e['_' + k] = self.tm(v)
        if e['type'] == 'cards':
            for i, it in enumerate(e['items']): e[f'_item{i}_at'] = self.tm(it.get('at', e.get('at', -1))) + it.get('delay', 0.0) if it.get('at', e.get('at', -1)) != -1 else -100.0

    def make_chunks(self):
        chunks = []
        for b, ph in enumerate(self.spec['phrases']):
            cap = ph.get('cap', ph['say']); ws = self.words[b]
            parts = [p.split() for p in cap.split('|')] if '|' in cap else auto_chunks(cap.split())
            n_cap = sum(len(p) for p in parts)
            s, e = self.times[b]
            if n_cap == len(ws):
                i = 0
                for p in parts:
                    chunks.append({'words': [(w, ws[i + j][1], ws[i + j][2]) for j, w in enumerate(p)]}); i += len(p)
            else:  # caption differs from the spoken words (numbers, names): spread by length
                tot = sum(len(w) + 2 for p in parts for w in p); x = s
                for p in parts:
                    wl = []
                    for w in p:
                        d = (e - s) * (len(w) + 2) / tot; wl.append((w, x, x + d)); x += d
                    chunks.append({'words': wl})
        for i, c in enumerate(chunks):
            c['start'] = c['words'][0][1] - 0.05; end_spoken = c['words'][-1][2]
            if i + 1 < len(chunks):
                nxt = chunks[i + 1]['words'][0][1] - 0.05
                c['end'] = nxt if nxt - end_spoken < 0.9 else end_spoken + 0.35
            else:
                c['end'] = end_spoken + 0.4
        return chunks

def auto_chunks(words, n=4):
    """split a caption into readable chunks of up to n words, breaking after commas and sentence ends"""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= n or w.endswith((',', '.', '?', '!', ':')):
            out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def draw_els(cv, els, t, scene_start):
    for e in els:
        t0 = e['_t0'] if e['_t0'] > -50 else scene_start - 100
        lt = t - t0
        if e['_t0'] > -50 and lt < 0 and e['type'] not in ('bg', 'ground', 'cards', 'mascot'): continue
        if e.get('_until') is not None and t > e['_until'] - 0.0:
            fo = clamp((t - e['_until']) / 0.2)
            if fo >= 1: continue
            cv.saveLayerAlpha(None, int(255 * (1 - fo)))
        def R(name, e=e):
            v = e.get('_' + name + '_at')
            return t - v if v is not None else -100.0
        if e['type'] in ('bg', 'ground'): lt = t - scene_start
        if e['type'] == 'mascot' and e['_t0'] < -50: lt = t - scene_start   # hook gambler walks in from frame 0
        DRAW[e['type']](cv, e, max(lt, 0) if e['type'] not in ('bg',) else lt, R)
        if e.get('_until') is not None and t > e['_until']: cv.restore()

def is_kw(w, kw):
    k = w.strip(",.'?!:").lower()
    return k in kw or any(ch.isdigit() for ch in k) or k.startswith('$')

def captions(cv, tl, t):
    for c in tl.chunks:
        if c['start'] <= t < c['end']:
            words = c['words']; f = font('Inter-Black', 84); sp = f.measureText(' ')
            disp = [w[0].upper() for w in words]; wid = [f.measureText(d) for d in disp]
            lines, cur, cw = [], [], 0
            for i, wd in enumerate(wid):
                if cur and cw + sp + wd > 900: lines.append(cur); cur, cw = [], 0
                cur.append(i); cw += (sp if cw else 0) + wd
            lines.append(cur)
            s = 0.85 + 0.15 * back_out(clamp((t - c['start']) / 0.18), 2.0)
            lh = 94; y0 = CAP_Y - (len(lines) - 1) * lh / 2
            cv.save(); cv.translate(W / 2, CAP_Y); cv.scale(s, s); cv.translate(-W / 2, -CAP_Y)
            for li, ln in enumerate(lines):
                lw = sum(wid[i] for i in ln) + sp * (len(ln) - 1); x = W / 2 - lw / 2; y = y0 + li * lh
                for i in ln:
                    w, ws = words[i][0], words[i][1]
                    cc = GOLD if is_kw(w, tl.kw) else PAPER
                    cv.drawString(disp[i], x + 4, y + 7, f, paint('#000000', 0.55, blur=6))
                    cv.drawString(disp[i], x, y, f, paint('#000000', 1, 'stroke', 14))
                    cv.drawString(disp[i], x, y, f, paint(cc, 1.0 if ws <= t else 0.5))
                    x += wid[i] + sp
            cv.restore(); break

def progress(cv, tl, t):
    pts = tl.spec.get('progress') or []
    if not pts: return
    ts = [tl.tm(p) + 0.05 for p in pts]
    if t < ts[0] - 0.1 or t > tl.tm(tl.spec.get('progress_end', 'end')): return
    n = len(ts); done = sum(1 for x in ts if t >= x)
    for k in range(n):
        x = W / 2 - (n - 1) * 23 + k * 46; on = k < done
        pop = back_out(clamp((t - ts[k]) / 0.25), 2.5) if on else 1
        if on: cv.drawCircle(x, 150, 15 * pop, paint(RUST if k == n - 1 else GOLD))
        else: cv.drawCircle(x, 150, 13, paint(PAPER, 0.6, 'stroke', 3))

def frame(cv, tl, t):
    cur = [s for s in tl.scenes if s['start'] <= t < s['end']] or [tl.scenes[-1]]
    sc = cur[0]
    cv.save(); draw_els(cv, sc['els'], t, sc['start']); cv.restore()
    nxt = [s for s in tl.scenes if s['start'] > sc['start'] and s['start'] - XF <= t < s['start']]
    if nxt:
        cv.saveLayerAlpha(None, int(255 * ease_in_out((t - (nxt[0]['start'] - XF)) / XF)))
        draw_els(cv, nxt[0]['els'], t, nxt[0]['start']); cv.restore()
    fb = font('Mono-Bold', 26); txt = f"THE RIGGED GAME  |  EP {tl.spec.get('episode', '00')}"; bw = fb.measureText(txt)
    cv.drawRoundRect(skia.Rect(W / 2 - bw / 2 - 22, 64, W / 2 + bw / 2 + 22, 108), 22, 22, paint(INKD, 0.75))
    text_c(cv, txt, W / 2, 95, fb, paint(PAPER, 0.9))
    progress(cv, tl, t)
    captions(cv, tl, t)
    if t > tl.dur - 0.45: cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', (t - (tl.dur - 0.45)) / 0.45))

def still(tl, t, path):
    surf = skia.Surface(W, H); cv = surf.getCanvas(); cv.clear(skia.ColorBLACK); frame(cv, tl, t)
    surf.makeImageSnapshot().save(path, skia.kPNG)

def render_part(args):
    spec_path, timing_path, a, b, out = args
    import json
    spec = json.load(open(spec_path)); tm = json.load(open(timing_path))
    tl = Timeline(spec, tm['times'], tm['words'], tm['total'])
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}',
                           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14',
                           '-profile:v', 'high', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(a, b):
        cv.clear(skia.ColorBLACK); frame(cv, tl, i / FPS)
        ff.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
    ff.stdin.close(); ff.wait()

def render_video(spec_path, timing_path, wav, out_mp4, dur, workers=None):
    """near-lossless H.264 (CRF 14, high profile) + AAC 192k; frames rendered in parallel parts"""
    from multiprocessing import Pool
    n = int(round(dur * FPS)); workers = workers or max(1, min(4, os.cpu_count() or 1))
    cuts = [n * k // workers for k in range(workers + 1)]
    parts = [out_mp4 + f'.part{k}.mp4' for k in range(workers)]
    with Pool(workers) as p:
        p.map(render_part, [(spec_path, timing_path, cuts[k], cuts[k + 1], parts[k]) for k in range(workers)])
    lst = out_mp4 + '.list.txt'
    open(lst, 'w').write(''.join(f"file '{os.path.abspath(x)}'\n" for x in parts))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', wav,
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', f'apad,afade=t=out:st={dur - 0.6:.2f}:d=0.6',
                    '-c:a', 'aac', '-b:a', '192k', '-t', f'{dur:.2f}', '-movflags', '+faststart', out_mp4], check=True)
    for x in parts + [lst]: os.remove(x)

def cover(spec, path):
    """1080x1920 cover: rays, gambler, kicker, big cut-out word, sub line"""
    c = spec.get('cover', {})
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    d_bg(cv, {'look': 'dark', 'rays': True}, 0.0, lambda n: -100)
    mascot_draw(cv, W / 2, 1080, 0.95, 1.0, '#000000')
    if c.get('kicker'): label_card(cv, c['kicker'], W / 2, 330, 56, INKD, GOLD, rot=-3, fname='Inter-Black')
    if c.get('big'):
        f = font('Playfair-Black', 200); w = f.measureText(c['big'])
        cv.save(); cv.translate(W / 2, 700); cv.rotate(-3)
        cut(cv, rect_path(-w / 2 - 40, -180, w / 2 + 40, 52), PAPER, 12, 16, 0.5); text_c(cv, c['big'], 0, 0, f, paint(INKD)); cv.restore()
    if c.get('sub'): label_card(cv, c['sub'], W / 2, 860, 50, RUST, PAPER, rot=2, fname='Inter-Black')
    cut(cv, rect_path(-50, 1500, W + 50, H), GROUND, 0, -10, 0.35)
    fb = font('Mono-Bold', 34); text_c(cv, 'THE RIGGED GAME', W / 2, 1640, fb, paint(PAPER, 0.85))
    surf.makeImageSnapshot().save(path, skia.kPNG)
