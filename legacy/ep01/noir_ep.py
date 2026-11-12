"""The Rigged Game EP01, noir paper cutout edition."""
import math, random, sys, subprocess
import skia
from render import (W, H, FPS, DUR, C, font, paint, text_c, glow, clamp, ease_out, ease_in_out,
                    back_out, prog, wheel, gear_path, ORDER, HOT, BARS)
from styles import cut, casino_sil, casino_windows, man_path, palm, paper_bg, noir
from timing import caption_chunks, EMPHASIS

PAPER = '#f6ecd4'; INKD = '#1a100b'; BROWN = '#6b4630'; RUST = '#b3261e'; AMBER = '#e8b04a'
GROUND = '#1a100b'; SHADOW = '#050302'
BP = '#16477a'; BP_LINE = '#eaf4ff'; BP_HI = '#ffcf5a'

def P():
    return skia.Path()

def rect_path(l, t, r, b):
    p = P(); p.addRect(skia.Rect(l, t, r, b)); return p

def circ_path(x, y, r):
    p = P(); p.addCircle(x, y, r); return p

def ground(cv, y=1250, color=GROUND):
    cut(cv, rect_path(-50, y, W + 50, H), color, 0, -10, 0.35)

def label(cv, text, x, y, size=44, bg=RUST, fg=PAPER, rot=-3, fname='Mono-Bold', a=1.0, s=1.0):
    f = font(fname, size)
    w = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    cut(cv, rect_path(-w / 2 - 28, -size * 1.0, w / 2 + 28, size * 0.42), bg, 6, 9, 0.35 * a)
    text_c(cv, text, 0, 0, f, paint(fg, a))
    cv.restore()

def curtains(cv, t):
    # scalloped red curtains top and sides
    sway = math.sin(t * 1.2) * 6
    for side in (-1, 1):
        p = P()
        x0 = 0 if side < 0 else W
        p.moveTo(x0, 0)
        p.lineTo(x0 - side * -230, 0)
        p.cubicTo(x0 + side * -170 + sway, 500, x0 + side * -260, 900, x0 + side * -140 + sway, 1260)
        p.lineTo(x0, 1260); p.close()
        cut(cv, p, '#8e1d17', side * -10, 14, 0.4)
        for k in range(4):
            xx = x0 + side * -(40 + k * 45)
            cv.drawLine(xx, 0, xx + sway * 0.5, 1150 - k * 120, paint('#5e120e', 0.6, 'stroke', 5))
    top = P(); top.moveTo(0, 0); top.lineTo(W, 0); top.lineTo(W, 120)
    for k in range(6, -1, -1):
        x = k * W / 6
        top.quadTo(x + W / 12, 200, x, 120) if k < 6 else None
    top.lineTo(0, 120); top.close()
    cut(cv, top, '#a3241c', 0, 12, 0.4)

def chandelier(cv, x, y, t):
    cv.drawLine(x, 0, x, y, paint(SHADOW, 1, 'stroke', 5))
    p = P()
    p.addOval(skia.Rect(x - 120, y, x + 120, y + 40))
    for k in range(5):
        cx = x - 100 + k * 50
        p.addRect(skia.Rect(cx - 5, y - 40, cx + 5, y))
    cut(cv, p, SHADOW, 6, 10, 0.3)
    for k in range(5):
        cx = x - 100 + k * 50
        fl = 0.8 + 0.2 * math.sin(t * 9 + k)
        cv.drawCircle(cx, y - 48, 9 * fl, paint(AMBER))
        glow(cv, cx, y - 48, 60, '#ffb84a', 0.3 * fl)

# ---------------- scenes ----------------
def s_open(cv, t):
    noir(cv, t, cap_words=None)

def s_watch(cv, t):
    paper_bg(cv, '#e9d9b6', '#cdb48a')
    glow(cv, W / 2, 620, 520, '#ffd27a', 0.35)
    curtains(cv, t)
    chandelier(cv, W / 2, 260, t)
    # table
    tab = P(); tab.addOval(skia.Rect(60, 900, W - 60, 1260)); cut(cv, tab, '#2f5a3a', 8, 14, 0.45)
    zoom = 1 + 0.04 * t
    cv.save(); cv.translate(W / 2, 700); cv.scale(zoom, zoom); cv.translate(-W / 2, -700)
    cv.drawCircle(W / 2 + 10, 718, 300 * 1.1, paint('#000000', 0.35, blur=14))
    wheel(cv, W / 2, 700, 270, rot=t * 70)
    ba = math.radians(-t * 260)
    cv.drawCircle(W / 2 + math.cos(ba) * 262, 700 + math.sin(ba) * 262, 12, paint('#ffffff'))
    cv.restore()
    ground(cv, 1250)
    # the watcher, front layer, left
    up = ease_out(prog(t, 0, 0.8))
    cut(cv, man_path(205, 780 + 160 * (1 - up), 0.8), SHADOW, 14, 18, 0.5)
    # no bet chip, then eye
    a = ease_out(prog(t, 0.3, 0.8)) * (1 - prog(t, 1.3, 1.6))
    if a > 0:
        cv.save(); cv.translate(860, 1040); cv.scale(0.6 + 0.4 * a, 0.6 + 0.4 * a)
        cut(cv, circ_path(0, 0, 70), RUST, 6, 9, 0.4 * a)
        cv.drawCircle(0, 0, 52, paint(PAPER, a, 'stroke', 7))
        cv.drawLine(-85, -85, 85, 85, paint(PAPER, a, 'stroke', 14))
        cv.restore()
    b = ease_out(prog(t, 1.45, 1.9))
    if b > 0:
        cv.save(); cv.translate(860, 1040)
        e = P(); e.moveTo(-100, 0); e.quadTo(0, -80 * b, 100, 0); e.quadTo(0, 80 * b, -100, 0); e.close()
        cut(cv, e, PAPER, 6, 9, 0.4 * b)
        cv.drawCircle(0, 0, 34 * b, paint(INKD))
        cv.drawCircle(10, -10, 9 * b, paint('#ffffff'))
        cv.restore()

NB_R = random.Random(3)
NB = [NB_R.randint(0, 36) for _ in range(120)]

def s_notebook(cv, t):
    paper_bg(cv, '#3a2a1c', '#160e08')
    glow(cv, 820, 380, 520, '#ffb84a', 0.35)
    # candle
    cut(cv, rect_path(800, 400, 860, 640), PAPER, 6, 10, 0.4)
    fl = 1 + 0.08 * math.sin(t * 13)
    f = P(); f.moveTo(830, 330 - 20 * fl); f.quadTo(860, 380, 830, 400); f.quadTo(800, 380, 830, 330 - 20 * fl)
    cv.drawPath(f, paint(AMBER)); glow(cv, 830, 370, 140, '#ffcf6b', 0.5)
    # notebook page, cut-out
    cv.save(); cv.translate(W / 2, 760); cv.rotate(-4 + 1.2 * math.sin(t * 0.7)); cv.translate(-W / 2, -760)
    page = rect_path(130, 300, W - 150, 1170)
    cut(cv, page, PAPER, 14, 20, 0.55)
    for k in range(16):
        y = 390 + k * 48
        cv.drawLine(170, y, W - 190, y, paint('#9fb6c8', 0.5, 'stroke', 2))
    cv.drawLine(240, 300, 240, 1170, paint(RUST, 0.6, 'stroke', 3))
    fm = font('Mono-Bold', 34)
    shown = int(clamp(t / 3.3) * 96)
    for i in range(min(shown, 96)):
        r, c = divmod(i, 6)
        x = 270 + c * 108; y = 380 + r * 48
        if y > 1150: break
        cv.drawString(f'{NB[i]:>2}', x, y, fm, paint(INKD, 0.4 + 0.6 * clamp((shown - i) / 4)))
    # pen
    pr = min(shown, 95); r, c = divmod(pr, 6)
    px, py = 270 + c * 108 + 60, 380 + r * 48 - 10
    pen = P(); pen.moveTo(px, py); pen.lineTo(px + 26, py - 14); pen.lineTo(px + 230, py - 210)
    pen.lineTo(px + 214, py - 226); pen.lineTo(px + 12, py - 30); pen.close()
    cut(cv, pen, SHADOW, 10, 14, 0.45)
    cv.restore()
    ground(cv, 1255)
    day = 1 + int(clamp(t / 3.6) * 29)
    label(cv, f'DAY {day:02d} / 30', W / 2, 250, 46, RUST, PAPER, rot=-2)

def blueprint_card(cv, rot=2):
    cv.save(); cv.translate(W / 2, 720); cv.rotate(rot); cv.translate(-W / 2, -720)
    card = rect_path(80, 230, W - 80, 1180)
    cut(cv, card, BP, 14, 20, 0.5)
    cv.save(); cv.clipPath(card)
    glow(cv, W / 2, 700, 700, '#2f7fd0', 0.35)
    for x in range(80, W, 40):
        cv.drawLine(x, 230, x, 1180, paint('#ffffff', 0.10 if x % 200 else 0.2, 'stroke', 1.5))
    for y in range(230, 1180, 40):
        cv.drawLine(80, y, W - 80, y, paint('#ffffff', 0.10 if y % 200 else 0.2, 'stroke', 1.5))
    cv.restore()
    cv.restore()

def s_machines(cv, t):
    paper_bg(cv)
    blueprint_card(cv, 1.5)
    line = paint(BP_LINE, 0.95, 'stroke', 4)
    ga = 1 - prog(t, 1.25, 1.6)
    if ga > 0:
        lp = paint(BP_LINE, ga, 'stroke', 4)
        cv.drawPath(gear_path(430, 640, 220, 14, t * 40), lp)
        cv.drawPath(gear_path(430 + 340, 640 + 210, 140, 9, -t * 40 * 14 / 9 + 10), lp)
        cv.drawPath(gear_path(300, 960, 100, 8, -t * 40 * 14 / 8 + 5), lp)
        text_c(cv, 'FIG. 1  MACHINES', W / 2, 330, font('Mono-Bold', 36), paint(BP_HI, ga))
    b = ease_out(prog(t, 1.35, 1.9))
    if b > 0:
        wob = math.sin(t * 9) * 14 * clamp((t - 2.2) / 1.0)
        cx, cy, r = W / 2, 720, 300 * (0.75 + 0.25 * b)
        lp = paint(BP_LINE, b, 'stroke', 4)
        for rr in (r, r * 0.85, r * 0.55, r * 0.2):
            cv.drawCircle(cx + wob * (1 - rr / r), cy, rr, lp)
        rot = math.radians(t * 90)
        for i in range(37):
            a = rot + i * 2 * math.pi / 37
            cv.drawLine(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55,
                        cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85, paint(BP_LINE, 0.8 * b, 'stroke', 2))
        c = ease_out(prog(t, 2.2, 2.8))
        if c > 0:
            cv.drawLine(cx, 330, cx, 1110, paint(BP_LINE, 0.5 * c, 'stroke', 2))
            cv.drawCircle(cx, cy, 9, paint(BP_LINE, c))
            cv.drawCircle(cx + wob + 16, cy - 8, 12, paint(BP_HI, c))
            cv.drawLine(cx + wob + 16, cy - 8, cx + 290, cy - 330, paint(BP_HI, c, 'stroke', 3))
            cv.drawString('AXIS OFF CENTRE?', cx + 40, cy - 345, font('Mono-Bold', 32), paint(BP_HI, c))
            text_c(cv, 'FIG. 2  PERFECTLY BALANCED?', W / 2, 1110, font('Mono-Bold', 34), paint(BP_HI, c))
    ground(cv, 1260)

def s_flaw(cv, t):
    paper_bg(cv)
    glow(cv, W / 2, 520, 500, GOLD_GLOW, 0.0)
    move = ease_in_out(prog(t, 1.5, 2.3))
    R = 290 - 120 * move
    cy = 690 - 330 * move
    hl = ease_in_out(prog(t, 0.25, 1.1)) * (0.75 + 0.25 * math.sin(t * 6))
    cv.drawCircle(W / 2 + 12, cy + 18, R * 1.1, paint('#000000', 0.4, blur=14))
    wheel(cv, W / 2, cy, R, rot=t * 20, highlight=HOT, hl_amt=hl)
    g = ease_out(prog(t, 1.9, 3.4))
    if g > 0:
        x0, base, bw, gap = 95, 1150, 20, 4.3
        for i, (n, v) in enumerate(BARS):
            x = x0 + i * (bw + gap)
            h = 330 * v * ease_out(prog(t, 1.9 + i * 0.02, 3.0 + i * 0.02))
            col = RUST if n in HOT else BROWN
            cut(cv, rect_path(x, base - h, x + bw, base), col, 4, 6, 0.35 * g)
        avg = base - 330
        cv.drawLine(x0 - 10, avg, W - 80, avg, paint(INKD, 0.8 * g, 'stroke', 3))
        cv.drawString('EXPECTED', W - 270, avg - 14, font('Mono-Bold', 28), paint(INKD, g))
        label(cv, 'HOW OFTEN EACH NUMBER LANDED', W / 2, 1215, 30, INKD, PAPER, rot=0, a=g)
    ground(cv, 1262)

GOLD_GLOW = '#e2b84a'

def chip_stack(cv, x, base, n, color, w=130):
    if n <= 0: return
    p = rect_path(x - w / 2, base - n * 23, x + w / 2, base)
    cut(cv, p, color, 8, 12, 0.45)
    for k in range(n):
        y = base - k * 23
        cv.drawLine(x - w / 2, y, x + w / 2, y, paint('#000000', 0.35, 'stroke', 2))
        for j in range(4):
            sx = x - w / 2 + 18 + j * (w - 36) / 3
            cv.drawRect(skia.Rect(sx - 7, y - 19, sx + 7, y - 4), paint(PAPER, 0.85))

def s_win(cv, t):
    paper_bg(cv)
    glow(cv, W / 2, 700, 650, '#ffcf6b', 0.25 + 0.15 * clamp(t / 8))
    op = 1 - prog(t, 2.9, 3.3)
    if op > 0:
        cv.saveLayerAlpha(None, int(255 * op))
        cv.drawCircle(W / 2 + 12, 578, 300, paint('#000000', 0.4, blur=14))
        wheel(cv, W / 2, 560, 270, rot=0, highlight=HOT, hl_amt=0.75 + 0.25 * math.sin(t * 6))
        step = 360 / 37
        hot_idx = [i for i, n in enumerate(ORDER) if n in HOT]
        for k, i in enumerate(hot_idx):
            d = prog(t, 0.05 + k * 0.1, 0.35 + k * 0.1)
            if d <= 0: continue
            am = math.radians(i * step - 90)
            tx, ty = W / 2 + math.cos(am) * 270 * 0.78, 560 + math.sin(am) * 270 * 0.78
            y = ty - 500 * (1 - ease_out(d)); sc = 1.6 - 0.6 * ease_out(d)
            cut(cv, circ_path(tx, y, 25 * sc), RUST, 4, 7, 0.45)
            cv.drawCircle(tx, y, 17 * sc, paint(PAPER, 1, 'stroke', 4 * sc))
        fw = font('Playfair-Black', 66)
        for k in range(9):
            age = clamp((t - 1.35 - k * 0.155) / 0.2)
            if age <= 0: continue
            sc = back_out(age, 2.5)
            x = W / 2 - 4 * 104 + k * 104
            cv.save(); cv.translate(x, 1010); cv.rotate(-4 + (k % 3) * 4); cv.scale(sc, sc)
            cut(cv, rect_path(-44, -50, 44, 46), PAPER, 5, 8, 0.4)
            text_c(cv, 'W', 0, 22, fw, paint(RUST))
            cv.restore()
        cv.restore()
    cols = [RUST, INKD, BROWN, '#2f5a3a', RUST]
    for i, col in enumerate(cols):
        n = int(clamp((t - 3.0 - i * 0.2) / 4.0) * 20)
        chip_stack(cv, W / 2 - 320 + i * 160, 1200, n, col)
    a = ease_out(prog(t, 3.25, 3.6))
    if a > 0:
        val = int(2_000_000 * ease_in_out(prog(t, 3.4, 6.4)))
        f = font('Playfair-Black', 150); s = f'{val:,}'
        pop = 1 + (0.08 * math.exp(-(t - 6.4) * 6) if t > 6.4 else 0)
        w = f.measureText('2,000,000')
        cv.save(); cv.translate(W / 2, 400); cv.rotate(-2); cv.scale(pop, pop)
        cut(cv, rect_path(-w / 2 - 40, -150, w / 2 + 40, 50), PAPER, 10, 14, 0.45 * a)
        text_c(cv, s, 0, 0, f, paint(INKD, a))
        cv.restore()
        label(cv, 'FRANCS', W / 2, 520, 46, RUST, PAPER, rot=-2, a=a)
    m = ease_out(prog(t, 6.9, 7.4))
    if m > 0:
        label(cv, '= MILLIONS TODAY', W / 2, 640, 56, INKD, '#ffcf5a', rot=2, fname='Inter-Black', a=m,
              s=0.6 + 0.4 * back_out(m))
    ground(cv, 1255)

def s_patched(cv, t):
    paper_bg(cv, '#b8382c', '#5a1510')
    glow(cv, W / 2, 700, 600, '#ff8a5a', 0.25)
    # guards silhouettes either side
    up = ease_out(prog(t, 0.0, 0.7))
    cut(cv, man_path(130, 820 + 200 * (1 - up), 0.75), SHADOW, 12, 16, 0.5)
    cut(cv, man_path(W - 130, 820 + 200 * (1 - up), 0.75), SHADOW, -12, 16, 0.5)
    flash = math.exp(-((t - 2.1) ** 2) * 18) if t > 1.5 else 0
    cv.drawCircle(W / 2 + 12, 738, 330 * 1.1, paint('#000000', 0.45, blur=16))
    wheel(cv, W / 2, 720, 300, rot=t * 50, flash=flash)
    wa = ease_in_out(prog(t, 1.4, 2.6))
    if 0 < wa < 1:
        cv.save(); cv.translate(W / 2, 720); cv.rotate(-60 + 120 * wa)
        wr = P(); wr.addRoundRect(skia.Rect(-14, -400, 14, -150), 10, 10); wr.addCircle(0, -420, 46)
        cut(cv, wr, '#d9d2c4', 6, 10, 0.45)
        cv.drawRect(skia.Rect(-14, -480, 14, -420), paint('#8e2a20'))
        cv.restore()
    st = prog(t, 2.6, 2.9)
    if st > 0:
        s = 2.2 - 1.2 * ease_out(st); a = ease_out(st)
        cv.save(); cv.translate(W / 2, 730); cv.rotate(-10); cv.scale(s, s)
        f = font('Inter-Black', 150); w = f.measureText('PATCHED')
        cut(cv, rect_path(-w / 2 - 40, -140, w / 2 + 40, 50), PAPER, 10, 14, 0.5 * a)
        text_c(cv, 'PATCHED', 0, 0, f, paint(RUST, a))
        cv.restore()
    label(cv, 'THE CASINO FIGHTS BACK', W / 2, 250, 44, INKD, PAPER, rot=-2, a=ease_out(prog(t, 0, 0.4)))
    ground(cv, 1255)

def s_houses(cv, t):
    paper_bg(cv, '#f0c49a', '#c9764e')
    cut(cv, circ_path(W / 2 + 120 - t * 10, 760, 230), '#e8743b', 5, 8, 0.25)
    # far hills
    hills = P(); hills.moveTo(-100, 1000)
    hills.cubicTo(200, 820, 500, 900, 700, 860); hills.cubicTo(900, 820, 1100, 900, 1300, 880)
    hills.lineTo(1300, 1300); hills.lineTo(-100, 1300); hills.close()
    hills.offset(-t * 10, 0)
    cut(cv, hills, '#9a5a3a', 6, 8, 0.25)
    pan = -45 * t
    for i in range(7):
        x = -140 + i * 230 + pan
        rise = ease_out(prog(t, 0.08 * i, 0.08 * i + 0.5))
        y = 1255 + 260 * (1 - rise)
        h = P(); h.addRect(skia.Rect(x, y - 360, x + 230, y))
        roof = P(); roof.moveTo(x - 10, y - 360); roof.lineTo(x + 115, y - 470); roof.lineTo(x + 240, y - 360); roof.close()
        h.addPath(roof); h.addRect(skia.Rect(x + 160, y - 470, x + 190, y - 400))
        cut(cv, h, '#3a2418' if i % 2 else '#2c1a12', 10, 14, 0.45)
        for wx, wy in ((40, -300), (140, -300), (40, -180)):
            r = skia.Rect(x + wx, y + wy, x + wx + 50, y + wy + 70)
            cv.drawRect(r, paint(AMBER))
            glow(cv, r.centerX(), r.centerY(), 60, '#ffb84a', 0.25)
        for k in range(3):
            sy = y - 490 - ((t * 60 + k * 50) % 150)
            cv.drawCircle(x + 175 + math.sin(t * 2 + k) * 10, sy, 14 + k * 4, paint(PAPER, 0.35))
    ground(cv, 1255)
    label(cv, 'YORKSHIRE, ENGLAND', W / 2, 300, 44, RUST, PAPER, rot=-2, a=ease_out(prog(t, 0, 0.4)))

def s_end(cv, t):
    paper_bg(cv)
    glow(cv, W / 2, 760, 600, '#ffcf6b', 0.3)
    a = ease_out(prog(t, 0, 0.5))
    fL = font('Inter-Black', 190); wL = fL.measureText('LUCK')
    torn = prog(t, 3.05, 3.4)
    cv.save(); cv.translate(W / 2, 560); cv.rotate(-3 - 8 * ease_out(torn))
    cv.translate(0, 60 * ease_out(torn))
    al = a * (1 - 0.65 * torn)
    cut(cv, rect_path(-wL / 2 - 40, -175, wL / 2 + 40, 45), PAPER, 10, 14, 0.45 * al)
    text_c(cv, 'LUCK', 0, 0, fL, paint(INKD, al))
    if torn > 0:
        cv.drawLine(-wL / 2 - 30, -60, -wL / 2 - 30 + (wL + 60) * ease_out(prog(t, 3.05, 3.3)), -70, paint(RUST, 1, 'stroke', 24))
    cv.restore()
    m = prog(t, 4.2, 4.6)
    if m > 0:
        s = back_out(m, 2.2)
        fM = font('Playfair-Black', 210); wM = fM.measureText('MATHS')
        cv.save(); cv.translate(W / 2, 900); cv.rotate(2); cv.scale(s, s)
        cut(cv, rect_path(-wM / 2 - 40, -185, wM / 2 + 40, 50), INKD, 12, 16, 0.5)
        text_c(cv, 'MATHS', 0, 0, fM, paint('#ffcf5a'))
        cv.restore()
    e = ease_out(prog(t, 0.6, 1.3))
    if e > 0:
        label(cv, 'P(win) > 1/37', W / 2, 300, 40, RUST, PAPER, rot=2, a=e)
    ground(cv, 1255)
    b = ease_out(prog(t, 1.0, 1.6))
    text_c(cv, 'THE RIGGED GAME', W / 2, 1720, font('Mono-Bold', 34), paint(PAPER, 0.8 * b))

SCENES = [
    (0.00, 5.45, s_open), (5.45, 8.30, s_watch), (8.30, 12.10, s_notebook),
    (12.10, 16.90, s_machines), (16.90, 21.55, s_flaw), (21.55, 30.70, s_win),
    (30.70, 35.95, s_patched), (35.95, 38.30, s_houses), (38.30, DUR + 0.1, s_end),
]
XF = 0.35
CHUNKS = caption_chunks()
CAP_Y = 1440

def captions(cv, t):
    for c in CHUNKS:
        if c['start'] <= t < c['end']:
            words = c['words']
            f = font('Inter-Black', 84)
            sp = f.measureText(' ')
            disp = [w[0].upper() for w in words]
            wid = [f.measureText(d) for d in disp]
            lines, cur, cw = [], [], 0
            for i, wd in enumerate(wid):
                if cur and cw + sp + wd > 900:
                    lines.append(cur); cur, cw = [], 0
                cur.append(i); cw += (sp if cw else 0) + wd
            lines.append(cur)
            s = 0.85 + 0.15 * back_out(clamp((t - c['start']) / 0.18), 2.0)
            lh = 94; y0 = CAP_Y - (len(lines) - 1) * lh / 2
            cv.save(); cv.translate(W / 2, CAP_Y); cv.scale(s, s); cv.translate(-W / 2, -CAP_Y)
            for li, ln in enumerate(lines):
                lw = sum(wid[i] for i in ln) + sp * (len(ln) - 1)
                x = W / 2 - lw / 2; y = y0 + li * lh
                for i in ln:
                    w, ws = words[i][0], words[i][1]
                    key = w.strip(",.'").lower().replace("'s", "")
                    col = '#ffcf5a' if key in EMPHASIS else PAPER
                    cv.drawString(disp[i], x + 4, y + 7, f, paint('#000000', 0.55, blur=6))
                    cv.drawString(disp[i], x, y, f, paint('#000000', 1, 'stroke', 14))
                    cv.drawString(disp[i], x, y, f, paint(col, 1.0 if ws <= t else 0.5))
                    x += wid[i] + sp
            cv.restore()
            break

def frame(cv, t):
    cur = [x for x in SCENES if x[0] <= t < x[1]]
    s, e, fn = cur[0] if cur else SCENES[-1]
    cv.save(); fn(cv, t - s); cv.restore()
    nxt = [x for x in SCENES if x[0] > s and x[0] - XF <= t < x[0]]
    if nxt:
        ns, _, nfn = nxt[0]
        cv.saveLayerAlpha(None, int(255 * ease_in_out((t - (ns - XF)) / XF)))
        nfn(cv, t - ns); cv.restore()
    fb = font('Mono-Bold', 26); bw = fb.measureText('THE RIGGED GAME  |  EP 01')
    cv.drawRoundRect(skia.Rect(W / 2 - bw / 2 - 22, 64, W / 2 + bw / 2 + 22, 108), 22, 22, paint(INKD, 0.75))
    text_c(cv, 'THE RIGGED GAME  |  EP 01', W / 2, 95, fb, paint(PAPER, 0.9))
    captions(cv, t)
    if t > DUR - 0.25:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', (t - (DUR - 0.25)) / 0.25))

def main():
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    if sys.argv[1] == 'stills':
        for tt in [float(x) for x in sys.argv[2:]]:
            cv.clear(skia.ColorBLACK); frame(cv, tt)
            surf.makeImageSnapshot().save(f'nstills/f_{tt:05.2f}.png', skia.kPNG)
        return
    a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba',
                           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast',
                           '-crf', '14', '-profile:v', 'high', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(a, b):
        cv.clear(skia.ColorBLACK); frame(cv, i / FPS)
        ff.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
    ff.stdin.close(); ff.wait()

if __name__ == '__main__':
    main()
