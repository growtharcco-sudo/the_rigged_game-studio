import math, random, sys, subprocess
import numpy as np
import skia
from timing import caption_chunks, EMPHASIS

W, H, FPS = 1080, 1920, 30
DUR = 43.55
NFRAMES = int(round(DUR * FPS))

# ---------- palette ----------
def C(hexs, a=255):
    hexs = hexs.lstrip('#')
    return skia.Color(int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16), a)

BG1 = '#06120d'; BG2 = '#0f2a1f'
GOLD = '#e2b84a'; GOLD_D = '#9c7a22'; CREAM = '#f4ead2'
RED = '#c8342b'; BLACK = '#141414'; GREEN = '#1f7a4a'; INK = '#2a2118'

TF = {n: skia.Typeface.MakeFromFile(f'fonts/{n}.ttf') for n in
      ['Inter-Black', 'Inter-Bold', 'Inter-Regular', 'Playfair-Black', 'Playfair-Bold', 'Mono-Bold']}

def font(name, size):
    f = skia.Font(TF[name], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f

# ---------- helpers ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in_out(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def back_out(x, s=1.7):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def prog(t, a, b): return clamp((t - a) / (b - a))

def paint(color, a=None, style='fill', sw=0, aa=True, blur=0):
    p = skia.Paint(AntiAlias=aa)
    col = C(color) if isinstance(color, str) else color
    if a is not None:
        col = skia.ColorSetA(col, int(clamp(a) * 255))
    p.setColor(col)
    if style == 'stroke':
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(sw)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

def text_c(cv, s, x, y, f, p):
    w = f.measureText(s)
    cv.drawString(s, x - w / 2, y, f, p)
    return w

def background(cv, t, top=BG2, bot=BG1):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, H)], [C(top), C(bot)]))
    cv.drawRect(skia.Rect(0, 0, W, H), p)

def vignette(cv):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial((W / 2, H * 0.45), H * 0.75,
                [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 170)], [0, 0.55, 1]))
    cv.drawRect(skia.Rect(0, 0, W, H), p)

def glow(cv, x, y, r, color, a=0.5):
    p = skia.Paint()
    col = C(color)
    p.setShader(skia.GradientShader.MakeRadial((x, y), r,
                [skia.ColorSetA(col, int(255 * a)), skia.ColorSetA(col, 0)]))
    cv.drawCircle(x, y, r, p)

rng = random.Random(7)
STARS = [(rng.uniform(0, W), rng.uniform(0, 900), rng.uniform(1.2, 3.2), rng.uniform(0, 6.28)) for _ in range(110)]
DUST = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4), rng.uniform(0.2, 0.6), rng.uniform(0, 6.28)) for _ in range(40)]

def dust(cv, t, color=GOLD):
    for x, y, r, sp, ph in DUST:
        yy = (y - t * 40 * sp) % H
        xx = x + math.sin(t * sp + ph) * 20
        cv.drawCircle(xx, yy, r, paint(color, 0.18 + 0.12 * math.sin(t * 2 + ph)))

# ---------- roulette wheel ----------
ORDER = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33,
         1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
NUMF = font('Inter-Bold', 22)

def wedge_path(cx, cy, r0, r1, a0, a1):
    p = skia.Path()
    oval_o = skia.Rect(cx - r1, cy - r1, cx + r1, cy + r1)
    oval_i = skia.Rect(cx - r0, cy - r0, cx + r0, cy + r0)
    p.arcTo(oval_o, a0, a1 - a0, True)
    p.arcTo(oval_i, a1, a0 - a1, False)
    p.close()
    return p

def wheel(cv, cx, cy, R, rot, highlight=None, hl_amt=0.0, dividers=1.0, flash=0.0):
    s = R / 300.0
    # outer wooden rim
    cv.drawCircle(cx, cy + 14 * s, R * 1.08, paint('#000000', 0.5, blur=20 * s))
    rim = skia.Paint(AntiAlias=True)
    rim.setShader(skia.GradientShader.MakeRadial((cx - R * 0.3, cy - R * 0.3), R * 1.6,
                  [C('#7a4a22'), C('#3b210e'), C('#1e1006')]))
    cv.drawCircle(cx, cy, R * 1.08, rim)
    cv.drawCircle(cx, cy, R * 1.08, paint(GOLD, 0.8, 'stroke', 4 * s))
    cv.drawCircle(cx, cy, R * 0.98, paint('#120a04'))
    n = 37
    step = 360 / n
    for i, num in enumerate(ORDER):
        a0 = rot + i * step - 90 - step / 2
        col = GREEN if num == 0 else (RED if i % 2 == 1 else BLACK)
        cv.drawPath(wedge_path(cx, cy, R * 0.62, R * 0.95, a0, a0 + step), paint(col))
        if highlight and num in highlight and hl_amt > 0:
            cv.drawPath(wedge_path(cx, cy, R * 0.62, R * 0.95, a0, a0 + step),
                        paint(GOLD, 0.85 * hl_amt))
        # number
        am = math.radians(a0 + step / 2)
        cv.save()
        cv.translate(cx + math.cos(am) * R * 0.85, cy + math.sin(am) * R * 0.85)
        cv.rotate(a0 + step / 2 + 90)
        f = skia.Font(TF['Inter-Bold'], 22 * s)
        lab = str(num)
        tc = INK if (highlight and num in highlight and hl_amt > 0.5) else CREAM
        cv.drawString(lab, -f.measureText(lab) / 2, 8 * s, f, paint(tc))
        cv.restore()
        # divider
        a = math.radians(a0)
        dcol = GOLD if flash <= 0 else '#ffffff'
        cv.drawLine(cx + math.cos(a) * R * 0.62, cy + math.sin(a) * R * 0.62,
                    cx + math.cos(a) * R * 0.95, cy + math.sin(a) * R * 0.95,
                    paint(dcol, 0.7 * dividers + 0.3 * flash, 'stroke', (2 + 3 * flash) * s))
    # pocket ring
    cv.drawCircle(cx, cy, R * 0.62, paint(GOLD, 0.9, 'stroke', 3 * s))
    # cone
    cone = skia.Paint(AntiAlias=True)
    cone.setShader(skia.GradientShader.MakeRadial((cx - R * 0.15, cy - R * 0.15), R * 0.7,
                   [C('#8a5a2c'), C('#4a2a10'), C('#24140a')]))
    cv.drawCircle(cx, cy, R * 0.6, cone)
    # turret spokes
    for k in range(4):
        a = math.radians(rot + k * 90)
        cv.drawLine(cx, cy, cx + math.cos(a) * R * 0.32, cy + math.sin(a) * R * 0.32,
                    paint(GOLD, 1, 'stroke', 10 * s))
        cv.drawCircle(cx + math.cos(a) * R * 0.32, cy + math.sin(a) * R * 0.32, 11 * s, paint(GOLD))
    cv.drawCircle(cx, cy, 30 * s, paint(GOLD))
    cv.drawCircle(cx, cy, 30 * s, paint('#fff3c4', 0.6, 'stroke', 3 * s))
    # highlight sheen
    sh = skia.Paint(AntiAlias=True)
    sh.setShader(skia.GradientShader.MakeLinear([(cx - R, cy - R), (cx + R, cy + R)],
                 [skia.Color(255, 255, 255, 40), skia.Color(255, 255, 255, 0), skia.Color(0, 0, 0, 60)]))
    cv.drawCircle(cx, cy, R * 1.08, sh)

# ---------- scene 1: casino facade ----------
def casino(cv, cx, base, sc, lit):
    def R(x, y, w, h): return skia.Rect(cx + x * sc, base + y * sc, cx + (x + w) * sc, base + (y + h) * sc)
    body = skia.Paint(AntiAlias=True)
    body.setShader(skia.GradientShader.MakeLinear([(0, base - 500 * sc), (0, base)],
                   [C('#2b3a30'), C('#141d17')]))
    # wings
    cv.drawRect(R(-430, -300, 860, 300), body)
    # towers
    for tx in (-430, 330):
        cv.drawRect(R(tx, -470, 100, 470), body)
        p = skia.Path(); p.moveTo(cx + tx * sc, base - 470 * sc)
        p.quadTo(cx + (tx + 50) * sc, base - 600 * sc, cx + (tx + 100) * sc, base - 470 * sc); p.close()
        cv.drawPath(p, body)
        cv.drawLine(cx + (tx + 50) * sc, base - 560 * sc, cx + (tx + 50) * sc, base - 630 * sc, paint(GOLD, 0.9, 'stroke', 4 * sc))
        cv.drawCircle(cx + (tx + 50) * sc, base - 632 * sc, 7 * sc, paint(GOLD))
        for k in range(3):
            win = R(tx + 30, -420 + k * 120, 40, 70)
            cv.drawRoundRect(win, 18 * sc, 18 * sc, paint('#ffcf6b', 0.85 * lit))
            glow(cv, win.centerX(), win.centerY(), 70 * sc, '#ffb84a', 0.25 * lit)
    # central block and dome
    cv.drawRect(R(-180, -380, 360, 380), body)
    p = skia.Path(); p.moveTo(cx - 180 * sc, base - 380 * sc)
    p.cubicTo(cx - 170 * sc, base - 560 * sc, cx + 170 * sc, base - 560 * sc, cx + 180 * sc, base - 380 * sc); p.close()
    cv.drawPath(p, body)
    cv.drawPath(p, paint(GOLD, 0.55, 'stroke', 3 * sc))
    # clock
    cv.drawCircle(cx, base - 440 * sc, 34 * sc, paint(CREAM, 0.9 * lit))
    cv.drawCircle(cx, base - 440 * sc, 34 * sc, paint(GOLD, 1, 'stroke', 4 * sc))
    cv.drawLine(cx, base - 440 * sc, cx, base - 462 * sc, paint(INK, 1, 'stroke', 3 * sc))
    cv.drawLine(cx, base - 440 * sc, cx + 15 * sc, base - 440 * sc, paint(INK, 1, 'stroke', 3 * sc))
    # arched windows
    for wx in list(range(-400, -200, 70)) + list(range(220, 400, 70)) + [-130, -40, 50]:
        top = -250 if abs(wx) > 180 else -330
        hh = 170 if abs(wx) > 180 else 240
        win = R(wx + 10, top, 44, hh)
        cv.drawRoundRect(win, 22 * sc, 22 * sc, paint('#ffcf6b', 0.9 * lit))
        glow(cv, win.centerX(), win.centerY(), 90 * sc, '#ffb84a', 0.18 * lit)
    # cornice lines
    for yy in (-300, -380):
        cv.drawLine(cx - 440 * sc, base + yy * sc, cx + 440 * sc, base + yy * sc, paint(GOLD, 0.5, 'stroke', 3 * sc))
    # stairs
    for k in range(4):
        cv.drawRect(R(-220 - k * 25, k * 18, 440 + k * 50, 18), paint('#3a4a3f' if k % 2 else '#2c3a31'))

def scene_casino(cv, t):
    background(cv, t, '#0b1f33', '#081410')
    for x, y, r, ph in STARS:
        cv.drawCircle(x, y, r, paint(CREAM, 0.35 + 0.35 * math.sin(t * 2.5 + ph)))
    glow(cv, 820, 300, 160, '#fff1c9', 0.25)
    cv.drawCircle(820, 300, 60, paint('#fff4d6'))
    zoom = 1.0 + 0.06 * t
    cv.save()
    cv.translate(W / 2, 1150); cv.scale(zoom, zoom); cv.translate(-W / 2, -1150)
    # ground
    cv.drawRect(skia.Rect(-200, 1150, W + 200, H), paint('#0a120e'))
    lit = 0.4 + 0.6 * ease_out(prog(t, 0.3, 1.8))
    casino(cv, W / 2, 1150, 1.05, lit)
    # lamp posts
    for lx in (120, W - 120):
        cv.drawLine(lx, 1150, lx, 900, paint('#1b1b1b', 1, 'stroke', 8))
        cv.drawCircle(lx, 890, 16, paint('#ffe08a'))
        glow(cv, lx, 890, 120, '#ffc960', 0.35)
    cv.restore()
    # title
    a = ease_out(prog(t, 0.0, 0.8))
    f1 = font('Mono-Bold', 44)
    text_c(cv, 'MONTE CARLO', W / 2, 300 - 20 * (1 - a), f1, paint(GOLD, a))
    s = back_out(prog(t, 0.15, 0.9))
    f2 = font('Playfair-Black', 210)
    cv.save(); cv.translate(W / 2, 520); cv.scale(s, s)
    text_c(cv, '1800s', 4, 6, f2, paint('#000000', 0.5 * a, blur=8))
    text_c(cv, '1800s', 0, 0, f2, paint(CREAM, a))
    cv.restore()
    cv.drawLine(W / 2 - 160 * a, 590, W / 2 + 160 * a, 590, paint(GOLD, a, 'stroke', 4))

# ---------- scene 2: the watcher ----------
def man(cv, x, y, s, color='#0a0a0a', rim=0.0):
    p = skia.Path()
    # coat body
    p.moveTo(x - 150 * s, y + 520 * s)
    p.cubicTo(x - 160 * s, y + 250 * s, x - 120 * s, y + 140 * s, x - 60 * s, y + 120 * s)
    p.lineTo(x + 60 * s, y + 120 * s)
    p.cubicTo(x + 120 * s, y + 140 * s, x + 160 * s, y + 250 * s, x + 150 * s, y + 520 * s)
    p.close()
    cv.drawPath(p, paint(color))
    cv.drawCircle(x, y + 60 * s, 62 * s, paint(color))
    # top hat
    cv.drawRoundRect(skia.Rect(x - 95 * s, y + 5 * s, x + 95 * s, y + 25 * s), 8 * s, 8 * s, paint(color))
    cv.drawRect(skia.Rect(x - 58 * s, y - 120 * s, x + 58 * s, y + 10 * s), paint(color))
    cv.drawRect(skia.Rect(x - 58 * s, y - 20 * s, x + 58 * s, y + 0 * s), paint(GOLD, 0.6))
    if rim:
        cv.drawPath(p, paint(GOLD, 0.5 * rim, 'stroke', 4 * s))
        cv.drawCircle(x, y + 60 * s, 62 * s, paint(GOLD, 0.5 * rim, 'stroke', 4 * s))

def scene_watch(cv, t):
    background(cv, t, '#123426', '#06100b')
    # table felt
    felt = skia.Paint(AntiAlias=True)
    felt.setShader(skia.GradientShader.MakeRadial((W / 2, 700), 900, [C('#1d6b45'), C('#0c3122'), C('#06160f')]))
    cv.drawRect(skia.Rect(0, 0, W, H), felt)
    glow(cv, W / 2, 420, 500, '#ffd27a', 0.18)
    wheel(cv, W / 2, 640, 300, rot=t * 70)
    # ball orbiting
    ba = math.radians(-t * 260)
    cv.drawCircle(W / 2 + math.cos(ba) * 300 * 0.97, 640 + math.sin(ba) * 300 * 0.97, 13, paint('#ffffff'))
    # watcher silhouette rising from bottom
    up = ease_out(prog(t, 0.0, 0.9))
    man(cv, 230, 860 + 200 * (1 - up), 0.62, '#050806', rim=1.0)
    # "no bet" chip with cross
    a = ease_out(prog(t, 0.4, 1.0)) * (1 - prog(t, 1.4, 1.8))
    if a > 0:
        cx, cy = 840, 300
        cv.drawCircle(cx, cy, 70, paint(RED, a))
        cv.drawCircle(cx, cy, 54, paint(CREAM, a, 'stroke', 6))
        cv.drawLine(cx - 90, cy - 90, cx + 90, cy + 90, paint(CREAM, a, 'stroke', 14))
    # watching eye icon
    b = ease_out(prog(t, 1.6, 2.2))
    if b > 0:
        ex, ey = 840, 300
        p = skia.Path(); p.moveTo(ex - 90, ey)
        p.quadTo(ex, ey - 70 * b, ex + 90, ey); p.quadTo(ex, ey + 70 * b, ex - 90, ey); p.close()
        cv.drawPath(p, paint(CREAM, b))
        cv.drawCircle(ex, ey, 30 * b, paint(INK, b))
        cv.drawCircle(ex + 8, ey - 8, 8 * b, paint('#ffffff', b))

# ---------- scene 3: notebook ----------
NB_RNG = random.Random(3)
NB_NUMS = [NB_RNG.randint(0, 36) for _ in range(120)]

def scene_notebook(cv, t):
    background(cv, t, '#1a140c', '#0a0805')
    glow(cv, W / 2, 700, 700, '#ffcc66', 0.18)
    cv.save()
    cv.translate(W / 2, 760); cv.rotate(-3 + 1.5 * math.sin(t * 0.8)); cv.translate(-W / 2, -760)
    page = skia.Rect(110, 230, W - 110, 1160)
    cv.drawRoundRect(page.makeOffset(10, 18), 18, 18, paint('#000000', 0.5, blur=18))
    cv.drawRoundRect(page, 18, 18, paint(CREAM))
    for k in range(18):
        y = 330 + k * 50
        cv.drawLine(page.left() + 30, y, page.right() - 30, y, paint('#9fb6c8', 0.55, 'stroke', 2))
    cv.drawLine(page.left() + 110, page.top(), page.left() + 110, page.bottom(), paint(RED, 0.6, 'stroke', 3))
    # rings
    for k in range(9):
        cv.drawCircle(page.left() + 50, 290 + k * 105, 14, paint('#2a2a2a'))
    # numbers appearing
    f = font('Mono-Bold', 36)
    shown = int(clamp(t / 3.4) * 108)
    cols = 6
    for i in range(min(shown, 108)):
        r, c = divmod(i, cols)
        x = page.left() + 150 + c * 120
        y = 322 + r * 50
        if y > page.bottom() - 20: break
        age = clamp((shown - i) / 4)
        cv.drawString(f'{NB_NUMS[i]:>2}', x, y, f, paint(INK, 0.35 + 0.65 * age))
    cv.restore()
    # day counter
    day = 1 + int(clamp(t / 3.6) * 29)
    a = ease_out(prog(t, 0, 0.4))
    box = skia.Rect(W / 2 - 230, 1290, W / 2 + 230, 1300)
    f2 = font('Mono-Bold', 40)
    text_c(cv, f'DAY {day:02d} / 30', W / 2, 1240, f2, paint(GOLD, a))
    cv.drawRoundRect(skia.Rect(W / 2 - 220, 1262, W / 2 + 220, 1272), 5, 5, paint(GOLD, 0.25 * a))
    cv.drawRoundRect(skia.Rect(W / 2 - 220, 1262, W / 2 - 220 + 440 * day / 30, 1272), 5, 5, paint(GOLD, a))

# ---------- scene 4: machines / imperfect balance ----------
def gear_path(cx, cy, r, teeth, rot, depth=0.16):
    p = skia.Path()
    n = teeth * 4
    for i in range(n + 1):
        a = math.radians(rot) + 2 * math.pi * i / n
        rr = r if (i % 4) in (0, 1) else r * (1 - depth)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        if i == 0: p.moveTo(x, y)
        else: p.lineTo(x, y)
    p.close()
    p.addCircle(cx, cy, r * 0.35)
    p.setFillType(skia.PathFillType.kEvenOdd)
    return p

def scene_machines(cv, t):
    background(cv, t, '#14261f', '#060d0a')
    dust(cv, t)
    # phase A: gears (0 - 1.5s), phase B: wobbling wheel
    a_out = prog(t, 1.2, 1.7)
    if a_out < 1:
        al = 1 - a_out
        gp = skia.Paint(AntiAlias=True)
        gp.setShader(skia.GradientShader.MakeLinear([(0, 300), (0, 1100)], [C('#f3d27a'), C(GOLD_D)]))
        gp.setAlphaf(al)
        cv.drawPath(gear_path(430, 620, 230, 14, t * 40), gp)
        cv.drawPath(gear_path(430 + 230 + 120, 620 + 210, 150, 9, -t * 40 * 14 / 9 + 10), gp)
        cv.drawPath(gear_path(300, 960, 110, 8, -t * 40 * 14 / 8 + 5), gp)
    b = ease_out(prog(t, 1.4, 2.0))
    if b > 0:
        wob = math.sin(t * 9) * 10 * clamp((t - 2.2) / 1.0)
        cx, cy = W / 2 + wob, 700
        cv.save()
        cv.translate(W / 2, 700); cv.scale(0.7 + 0.3 * b, 0.7 + 0.3 * b); cv.translate(-W / 2, -700)
        wheel(cv, cx, cy, 300, rot=t * 90)
        cv.restore()
        # axis guide lines
        c = ease_out(prog(t, 2.2, 2.8))
        if c > 0:
            cv.drawLine(W / 2, 300, W / 2, 1100, paint(CREAM, 0.45 * c, 'stroke', 3))
            for yy in range(300, 1100, 40):
                pass
            cv.drawCircle(W / 2, 700, 10, paint(CREAM, c))
            cv.drawCircle(cx, cy, 10, paint(RED, c))
            f = font('Mono-Bold', 34)
            text_c(cv, 'PERFECTLY BALANCED?', W / 2, 1180, f, paint(GOLD, c))
            # off-balance meter
            mx = W / 2 + math.sin(t * 9) * 140
            cv.drawRoundRect(skia.Rect(W / 2 - 220, 230, W / 2 + 220, 246), 8, 8, paint(CREAM, 0.25 * c))
            cv.drawCircle(W / 2, 238, 6, paint(CREAM, c))
            cv.drawCircle(mx, 238, 18, paint(RED, c))

# ---------- scene 5: the flaw ----------
HOT = {7, 8, 9, 17, 18, 19, 22, 28, 29}  # illustrative "lucky pockets"
BAR_RNG = random.Random(11)
BARS = [(n, (1.0 + (0.55 if n in HOT else 0) + BAR_RNG.uniform(-0.12, 0.12))) for n in range(37)]

def scene_flaw(cv, t):
    background(cv, t, '#102a1e', '#050c08')
    # wheel shrinks to top, pockets glow
    hl = ease_in_out(prog(t, 0.3, 1.2)) * (0.75 + 0.25 * math.sin(t * 6))
    move = ease_in_out(prog(t, 1.6, 2.4))
    R = 300 - 110 * move
    cy = 700 - 290 * move
    glow(cv, W / 2, cy, R * 1.6, GOLD, 0.25 * hl)
    wheel(cv, W / 2, cy, R, rot=t * 20, highlight=HOT, hl_amt=hl)
    # bar chart
    g = ease_out(prog(t, 2.0, 3.6))
    if g > 0:
        x0, base, bw, gap = 90, 1180, 20, 4.3
        cv.drawLine(x0 - 10, base, W - 80, base, paint(CREAM, 0.6 * g, 'stroke', 3))
        avg_y = base - 300
        for i, (n, v) in enumerate(BARS):
            x = x0 + i * (bw + gap)
            h = 300 * v * ease_out(prog(t, 2.0 + i * 0.02, 3.2 + i * 0.02))
            col = GOLD if n in HOT else '#5f7d6e'
            cv.drawRoundRect(skia.Rect(x, base - h, x + bw, base), 4, 4, paint(col, g))
        # expected line
        cv.drawLine(x0 - 10, avg_y, W - 80, avg_y, paint(CREAM, 0.8 * g, 'stroke', 3))
        f = font('Mono-Bold', 28)
        cv.drawString('EXPECTED', W - 260, avg_y - 14, f, paint(CREAM, 0.8 * g))
        f2 = font('Mono-Bold', 30)
        text_c(cv, 'HOW OFTEN EACH NUMBER LANDED', W / 2, base + 60, f2, paint(GOLD, g))

# ---------- scene 6: winning / chips / counter ----------
def chip_side(cv, x, y, w, color):
    h = 22
    cv.drawRoundRect(skia.Rect(x - w / 2, y - h, x + w / 2, y), 10, 10, paint(color))
    for k in range(5):
        sx = x - w / 2 + 12 + k * (w - 24) / 4
        cv.drawRect(skia.Rect(sx - 7, y - h + 3, sx + 7, y - 3), paint(CREAM, 0.85))
    cv.drawRoundRect(skia.Rect(x - w / 2, y - h, x + w / 2, y), 10, 10, paint('#000000', 0.35, 'stroke', 2))

def scene_win(cv, t):
    # local timeline: 0 = 21.61
    background(cv, t, '#0f2f22', '#05100b')
    glow(cv, W / 2, 800, 650, GOLD, 0.15 + 0.1 * clamp(t / 8))
    dust(cv, t)
    # stacks grow
    stacks = [(W / 2 - 300, RED), (W / 2 - 150, '#1b1b1b'), (W / 2, GOLD_D), (W / 2 + 150, '#1d5fa8'), (W / 2 + 300, RED)]
    for i, (sx, col) in enumerate(stacks):
        n = int(clamp((t - 3.0 - i * 0.2) / 4.0) * 21)
        for k in range(n):
            chip_side(cv, sx, 1180 - k * 23, 128, col)
    # counter
    c = ease_in_out(prog(t, 3.4, 6.4))
    val = int(2_000_000 * c)
    a = ease_out(prog(t, 3.25, 3.6))
    if a > 0:
        f = font('Playfair-Black', 150)
        s = f'{val:,}'
        pop = 1 + 0.08 * math.exp(-max(0, t - 6.4) * 6) * (t > 6.4)
        cv.save(); cv.translate(W / 2, 400); cv.scale(pop, pop)
        text_c(cv, s, 4, 6, f, paint('#000000', 0.5 * a, blur=10))
        text_c(cv, s, 0, 0, f, paint(GOLD, a))
        cv.restore()
        f2 = font('Mono-Bold', 50)
        text_c(cv, 'FRANCS', W / 2, 480, f2, paint(CREAM, a))
    # opening: chips land on the lucky pockets, then a winning streak
    op = 1 - prog(t, 2.9, 3.3)
    if op > 0:
        cv.saveLayerAlpha(None, int(255 * op))
        hl = 0.75 + 0.25 * math.sin(t * 6)
        wheel(cv, W / 2, 560, 290, rot=0, highlight=HOT, hl_amt=hl)
        step = 360 / 37
        hot_idx = [i for i, n in enumerate(ORDER) if n in HOT]
        for k, i in enumerate(hot_idx):
            d = prog(t, 0.05 + k * 0.1, 0.35 + k * 0.1)
            if d <= 0: continue
            am = math.radians(i * step - 90)
            tx, ty = W / 2 + math.cos(am) * 290 * 0.78, 560 + math.sin(am) * 290 * 0.78
            y = ty - 500 * (1 - ease_out(d))
            sc = 1.6 - 0.6 * ease_out(d)
            cv.drawCircle(tx, y + 6, 26 * sc, paint('#000000', 0.4, blur=4))
            cv.drawCircle(tx, y, 26 * sc, paint(GOLD_D))
            cv.drawCircle(tx, y, 18 * sc, paint(CREAM, 1, 'stroke', 4 * sc))
        # win streak
        f = font('Inter-Black', 60)
        wins = int(clamp((t - 1.35) / 1.4) * 9 + (1 if t > 1.35 else 0))
        for k in range(min(wins, 9)):
            x = W / 2 - 4 * 104 + k * 104
            age = clamp((t - 1.35 - k * 0.155) / 0.2)
            sc = back_out(age, 2.5)
            if sc <= 0: continue
            cv.save(); cv.translate(x, 1010); cv.scale(sc, sc)
            cv.drawRoundRect(skia.Rect(-44, -48, 44, 48), 16, 16, paint(GOLD))
            text_c(cv, 'W', 0, 22, f, paint(INK))
            cv.restore()
        cv.restore()
    # today's money
    m = ease_out(prog(t, 6.9, 7.5))
    if m > 0:
        f3 = font('Inter-Black', 64)
        box = skia.Rect(W / 2 - 330, 560, W / 2 + 330, 660)
        cv.drawRoundRect(box, 50, 50, paint(CREAM, m))
        text_c(cv, '= MILLIONS TODAY', W / 2, 632, f3, paint(INK, m))

# ---------- scene 7: patched ----------
def scene_patched(cv, t):
    background(cv, t, '#2a0f0d', '#0c0505')
    glow(cv, W / 2, 700, 650, RED, 0.18)
    flash = math.exp(-((t - 2.1) ** 2) * 18) if t > 1.5 else 0
    wheel(cv, W / 2, 720, 330, rot=t * 50, dividers=1.0, flash=flash)
    # wrench sweeping
    wa = ease_in_out(prog(t, 1.4, 2.6))
    if 0 < wa < 1:
        ang = -60 + 120 * wa
        cv.save(); cv.translate(W / 2, 720); cv.rotate(ang)
        p = paint('#cfd6dc')
        cv.drawRoundRect(skia.Rect(-14, -420, 14, -150), 10, 10, p)
        cv.drawCircle(0, -440, 46, p)
        cv.drawRect(skia.Rect(-14, -500, 14, -440), paint('#2a0f0d'))
        cv.restore()
    # stamp
    st = prog(t, 2.6, 2.9)
    if st > 0:
        s = 2.2 - 1.2 * ease_out(st)
        a = ease_out(st)
        cv.save(); cv.translate(W / 2, 720); cv.rotate(-12); cv.scale(s, s)
        f = font('Inter-Black', 150)
        w = f.measureText('PATCHED')
        box = skia.Rect(-w / 2 - 40, -140, w / 2 + 40, 50)
        cv.drawRoundRect(box, 20, 20, paint('#000000', 0.35 * a))
        cv.drawRoundRect(box, 20, 20, paint(RED, a, 'stroke', 14))
        text_c(cv, 'PATCHED', 0, 0, f, paint(RED, a))
        cv.restore()
    # header
    h = ease_out(prog(t, 0.0, 0.5))
    f2 = font('Mono-Bold', 42)
    text_c(cv, 'THE CASINO FIGHTS BACK', W / 2, 210, f2, paint(CREAM, h))

# ---------- scene 8: houses ----------
def scene_houses(cv, t):
    background(cv, t, '#3b2a4a', '#140d12')
    glow(cv, W / 2, 1050, 800, '#ff9c5a', 0.35)
    for x, y, r, ph in STARS[:40]:
        cv.drawCircle(x, y * 0.6, r * 0.8, paint(CREAM, 0.3 + 0.2 * math.sin(t * 3 + ph)))
    pan = -40 * t
    base = 1200
    cv.drawRect(skia.Rect(0, base, W, H), paint('#120c0c'))
    for i in range(7):
        x = -120 + i * 230 + pan
        rise = ease_out(prog(t, 0.1 * i, 0.1 * i + 0.6))
        y = base + 300 * (1 - rise)
        col = ['#5b3a2e', '#4a2f26', '#63412f'][i % 3]
        cv.drawRect(skia.Rect(x, y - 360, x + 230, y), paint(col))
        p = skia.Path(); p.moveTo(x - 10, y - 360); p.lineTo(x + 115, y - 470); p.lineTo(x + 240, y - 360); p.close()
        cv.drawPath(p, paint('#2a1c1a'))
        cv.drawRect(skia.Rect(x + 160, y - 470, x + 190, y - 400), paint('#2a1c1a'))
        for wx, wy in ((40, -300), (140, -300), (40, -180)):
            on = 0.5 + 0.5 * math.sin(t * 4 + i * 1.7 + wx)
            r = skia.Rect(x + wx, y + wy, x + wx + 50, y + wy + 70)
            cv.drawRect(r, paint('#ffcf6b', 0.75 + 0.25 * on))
            glow(cv, r.centerX(), r.centerY(), 60, '#ffb84a', 0.2)
        cv.drawRect(skia.Rect(x + 140, y - 140, x + 195, y), paint('#2a1c1a'))
        # smoke
        for k in range(3):
            sy = y - 480 - ((t * 60 + k * 50) % 150)
            cv.drawCircle(x + 175 + math.sin(t * 2 + k) * 10, sy, 14 + k * 4, paint(CREAM, 0.12))
    a = ease_out(prog(t, 0.0, 0.5))
    f = font('Mono-Bold', 44)
    text_c(cv, 'YORKSHIRE, ENGLAND', W / 2, 300, f, paint(GOLD, a))

# ---------- scene 9: end card ----------
def scene_end(cv, t):
    background(cv, t, '#0f2a1f', '#030806')
    dust(cv, t)
    glow(cv, W / 2, 760, 600, GOLD, 0.2)
    # LUCK appears then gets struck
    a = ease_out(prog(t, 0.0, 0.5))
    fL = font('Inter-Black', 190)
    luck_y = 560
    text_c(cv, 'LUCK', W / 2, luck_y, fL, paint(CREAM, a * (1 - 0.6 * prog(t, 3.3, 3.8))))
    st = ease_out(prog(t, 3.05, 3.35))
    if st > 0:
        w = fL.measureText('LUCK') + 60
        cv.drawLine(W / 2 - w / 2, luck_y - 65, W / 2 - w / 2 + w * st, luck_y - 65, paint(RED, 1, 'stroke', 22))
    # MATHS
    m = prog(t, 4.2, 4.6)
    if m > 0:
        s = back_out(m, 2.2)
        fM = font('Playfair-Black', 220)
        cv.save(); cv.translate(W / 2, 880); cv.scale(s, s)
        glow(cv, 0, -70, 380, GOLD, 0.35 * m)
        text_c(cv, 'MATHS', 0, 0, fM, paint(GOLD, clamp(m * 2)))
        cv.restore()
    # equation garnish
    e = ease_out(prog(t, 0.6, 1.4))
    if e > 0:
        f = font('Mono-Bold', 38)
        text_c(cv, 'P(win) > 1/37', W / 2, 320, f, paint(GOLD, e * 0.9))
    # brand
    b = ease_out(prog(t, 1.0, 1.6))
    fb = font('Mono-Bold', 34)
    text_c(cv, 'THE RIGGED GAME', W / 2, 1200, fb, paint(CREAM, 0.8 * b))
    cv.drawLine(W / 2 - 150 * b, 1225, W / 2 + 150 * b, 1225, paint(GOLD, b, 'stroke', 3))

# ---------- timeline ----------
SCENES = [
    (0.00, 5.45, scene_casino),
    (5.45, 8.30, scene_watch),
    (8.30, 12.10, scene_notebook),
    (12.10, 16.90, scene_machines),
    (16.90, 21.55, scene_flaw),
    (21.55, 30.70, scene_win),
    (30.70, 35.95, scene_patched),
    (35.95, 38.30, scene_houses),
    (38.30, DUR + 0.1, scene_end),
]
XF = 0.35  # crossfade seconds

CHUNKS = caption_chunks()
CAP_Y = 1440

def captions(cv, t):
    for c in CHUNKS:
        if c['start'] <= t < c['end']:
            words = c['words']
            fsz = 84
            f = font('Inter-Black', fsz)
            space = f.measureText(' ')
            disp = [w[0].upper() for w in words]
            widths = [f.measureText(d) for d in disp]
            # wrap into lines max 900px
            lines, cur, cw = [], [], 0
            for i, wd in enumerate(widths):
                if cur and cw + space + wd > 900:
                    lines.append(cur); cur, cw = [], 0
                cur.append(i); cw += (space if cw else 0) + wd
            lines.append(cur)
            age = t - c['start']
            pop = back_out(clamp(age / 0.18), 2.0)
            sc = 0.85 + 0.15 * pop
            lh = fsz * 1.12
            y0 = CAP_Y - (len(lines) - 1) * lh / 2
            cv.save(); cv.translate(W / 2, CAP_Y); cv.scale(sc, sc); cv.translate(-W / 2, -CAP_Y)
            for li, ln in enumerate(lines):
                lw = sum(widths[i] for i in ln) + space * (len(ln) - 1)
                x = W / 2 - lw / 2
                y = y0 + li * lh
                for i in ln:
                    w, ws, we = words[i][0], words[i][1], words[i][2]
                    key = w.strip(",.'").lower().replace("'s", "")
                    active = ws <= t
                    col = GOLD if key in EMPHASIS else '#ffffff'
                    alpha = 1.0 if active else 0.55
                    # stroke + shadow
                    cv.drawString(disp[i], x + 4, y + 7, f, paint('#000000', 0.55, blur=6))
                    cv.drawString(disp[i], x, y, f, paint('#000000', 1, 'stroke', 14))
                    cv.drawString(disp[i], x, y, f, paint(col, alpha))
                    x += widths[i] + space
            cv.restore()
            break

def brand_tag(cv, t):
    f = font('Mono-Bold', 26)
    a = 0.75
    text_c(cv, 'THE RIGGED GAME  |  EP 01', W / 2, 96, f, paint(CREAM, a * 0.8))

def draw_scene(cv, fn, t_local):
    cv.save(); fn(cv, t_local); cv.restore()

def render_frame(cv, t):
    active = [(s, e, fn) for s, e, fn in SCENES if s - XF <= t < e]
    # base: the scene containing t
    cur = [x for x in SCENES if x[0] <= t < x[1]]
    s, e, fn = cur[0] if cur else SCENES[-1]
    draw_scene(cv, fn, t - s)
    # incoming next scene crossfade
    nxt = [x for x in SCENES if x[0] > s and x[0] - XF <= t < x[0]]
    if nxt:
        ns, ne, nfn = nxt[0]
        a = ease_in_out((t - (ns - XF)) / XF)
        cv.saveLayerAlpha(None, int(255 * a))
        draw_scene(cv, nfn, t - ns)
        cv.restore()
    vignette(cv)
    brand_tag(cv, t)
    captions(cv, t)
    # final fade out
    if t > DUR - 0.25:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', (t - (DUR - 0.25)) / 0.25))

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'video'
    surf = skia.Surface(W, H)
    cv = surf.getCanvas()
    if mode == 'stills':
        for tt in [float(x) for x in sys.argv[2:]]:
            cv.clear(skia.ColorBLACK)
            render_frame(cv, tt)
            surf.makeImageSnapshot().save(f'stills/f_{tt:05.2f}.png', skia.kPNG)
        return
    a, b = int(sys.argv[2]), int(sys.argv[3])
    out = sys.argv[4]
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-profile:v', 'high',
                           '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(a, b):
        cv.clear(skia.ColorBLACK)
        render_frame(cv, i / FPS)
        img = surf.makeImageSnapshot()
        arr = img.toarray(colorType=skia.kRGBA_8888_ColorType)
        ff.stdin.write(arr.tobytes())
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    main()
