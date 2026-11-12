"""The Rigged Game EP02: Why casinos have no clocks. Noir paper cutout."""
import math, random, sys, subprocess, os
sys.path.insert(0, '/home/claude/jagger')
import skia
from render import (W, H, FPS, C, font, paint, text_c, glow, clamp, ease_out, ease_in_out,
                    back_out, prog, wheel)
from styles import cut, casino_sil, casino_windows, man_path, paper_bg
from noir_ep import (rect_path, circ_path, ground, label, curtains, chandelier, blueprint_card, chip_stack,
                     PAPER, INKD, RUST, AMBER, BROWN, SHADOW, BP_LINE, BP_HI)
from timing2 import caption_chunks, EMPHASIS, DUR

GREEN = '#2f5a3a'

def P(): return skia.Path()

def mascot(cv, x, y, s, a=1.0, color=SHADOW):
    """the channel's gambler: top hat, coat, cane"""
    if a < 1: cv.saveLayerAlpha(None, int(255 * a))
    cut(cv, man_path(x, y, s), color, 12 * s / 0.8, 16 * s / 0.8, 0.5)
    if a < 1: cv.restore()

def stamp(cv, text, x, y, t0, t, size=130, color=RUST, rot=-10, bg=PAPER):
    st = prog(t, t0, t0 + 0.28)
    if st <= 0: return
    s = 2.0 - 1.0 * ease_out(st); a = ease_out(st)
    f = font('Inter-Black', size); w = f.measureText(text)
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    cut(cv, rect_path(-w / 2 - 36, -size * 0.92, w / 2 + 36, size * 0.33), bg, 10, 14, 0.5 * a)
    cv.drawRoundRect(skia.Rect(-w / 2 - 22, -size * 0.8, w / 2 + 22, size * 0.21), 10, 10, paint(color, a, 'stroke', 8))
    text_c(cv, text, 0, 0, f, paint(color, a))
    cv.restore()

def hall(cv, t):
    paper_bg(cv, '#e9d9b6', '#cdb48a')
    glow(cv, W / 2, 620, 560, '#ffd27a', 0.3)
    curtains(cv, t)
    chandelier(cv, W / 2, 230, t)

# ---------- A: hunting for a clock ----------
def s_clock_hunt(cv, t):
    hall(cv, t)
    # wall panel with the pale mark where a clock should hang
    panel = rect_path(250, 380, W - 250, 1000)
    cut(cv, panel, '#7a5236', 10, 14, 0.45)
    for k in range(5):
        cv.drawLine(250, 420 + k * 130, W - 250, 420 + k * 130, paint('#5e3d27', 0.6, 'stroke', 3))
    cx, cy = W / 2, 640
    cv.drawCircle(cx, cy, 150, paint('#8f6646'))
    dash = paint(PAPER, 0.8, 'stroke', 6)
    dash.setPathEffect(skia.DashPathEffect.Make([26, 18], t * 30))
    cv.drawCircle(cx, cy, 150, dash)
    cv.drawCircle(cx, cy - 150 - 30, 9, paint(SHADOW))  # bare nail
    ground(cv, 1250)
    # the gambler walks in from the left
    walk = ease_out(prog(t, 0, 1.4))
    mascot(cv, -60 + 260 * walk, 820, 0.78)
    # magnifying glass sweeping the wall
    m = ease_out(prog(t, 0.6, 1.0))
    if m > 0 and t < 3.25:
        ang = t * 2.2
        mx, my = cx + math.cos(ang) * 230, cy + math.sin(ang * 1.3) * 170
        cv.save(); cv.translate(mx, my)
        cv.saveLayerAlpha(None, int(255 * m))
        hnd = P(); hnd.addRoundRect(skia.Rect(55, 55, 85, 230), 14, 14)
        hm = skia.Matrix(); hm.setRotate(-35); hnd.transform(hm)
        cut(cv, hnd, SHADOW, 6, 10, 0.4)
        cv.drawCircle(0, 0, 95, paint('#ffffff', 0.18))
        ring = P(); ring.addCircle(0, 0, 95); ring.addCircle(0, 0, 78); ring.setFillType(skia.PathFillType.kEvenOdd)
        cut(cv, ring, SHADOW, 6, 10, 0.4)
        cv.restore(); cv.restore()
    stamp(cv, 'NOT FOUND', W / 2, 660, 3.15, t, 120, RUST, -8)

# ---------- B: no clocks, no windows, no sunset ----------
def card_frame(cv, y, t_in, t, rot):
    a = ease_out(prog(t, t_in, t_in + 0.3))
    if a <= 0: return None
    cv.save(); cv.translate(W / 2 + (1 - a) * 900, y); cv.rotate(rot)
    r = skia.Rect(-400, -165, 400, 165)
    cut(cv, rect_path(r.left(), r.top(), r.right(), r.bottom()), PAPER, 10, 14, 0.45)
    return r

def s_three(cv, t):
    paper_bg(cv, '#3a2a1c', '#160e08')
    glow(cv, W / 2, 700, 700, '#ffb84a', 0.18)
    f = font('Inter-Black', 54)
    # card 1: clock, crossed
    r = card_frame(cv, 330, 0.0, t, -2)
    if r:
        cv.drawCircle(-230, 0, 110, paint('#ffffff')); cv.drawCircle(-230, 0, 110, paint(INKD, 1, 'stroke', 10))
        hand = t * 4
        cv.drawLine(-230, 0, -230 + math.cos(hand) * 80, math.sin(hand) * 80, paint(INKD, 1, 'stroke', 9))
        cv.drawLine(-230, 0, -230, -60, paint(INKD, 1, 'stroke', 9))
        x = ease_out(prog(t, 0.35, 0.6))
        if x > 0:
            cv.drawLine(-340, -110, -340 + 220 * x, -110 + 220 * x, paint(RUST, 1, 'stroke', 18))
            cv.drawLine(-120, -110, -120 - 220 * x, -110 + 220 * x, paint(RUST, 1, 'stroke', 18))
        cv.drawString('NO CLOCKS', -70, 20, f, paint(INKD))
        cv.restore()
    # card 2: window bricked up
    r = card_frame(cv, 700, 0.85, t, 2)
    if r:
        wr = skia.Rect(-330, -120, -130, 120)
        cv.drawRect(wr, paint('#9ec6e0'))
        cv.drawCircle(-230, -20, 40, paint('#ffd36b'))
        b = prog(t, 1.0, 1.8)
        rows = int(b * 8 + 0.999) if b > 0 else 0
        for rr in range(rows):
            y = 120 - (rr + 1) * 30
            off = 0 if rr % 2 else 25
            for cc in range(-1, 5):
                bx = -330 + off + cc * 50
                br = skia.Rect(max(bx, -330), y, min(bx + 48, -130), y + 28)
                if br.width() > 0: cv.drawRect(br, paint('#9b4a32'))
        cv.drawRect(wr, paint(INKD, 1, 'stroke', 8))
        cv.drawString('NO WINDOWS', -70, 20, f, paint(INKD))
        cv.restore()
    # card 3: the sunset sinks out of the frame
    r = card_frame(cv, 1070, 1.85, t, -1.5)
    if r:
        sky = skia.Rect(-370, -135, -110, 135)
        d = ease_in_out(prog(t, 2.1, 3.7))
        sp = skia.Paint()
        sp.setShader(skia.GradientShader.MakeLinear([(0, -135), (0, 135)],
                     [C('#f0a060') if d < 0.5 else C('#1b2a45'), C('#e8743b') if d < 0.5 else C('#0b1222')]))
        cv.drawRect(sky, sp)
        cv.save(); cv.clipRect(sky)
        cv.drawCircle(-240, -30 + 220 * d, 60, paint('#ffd36b', 1 - 0.6 * d))
        cv.drawRect(skia.Rect(-370, 70, -110, 135), paint('#2a1c12'))
        cv.restore()
        cv.drawRect(sky, paint(INKD, 1, 'stroke', 8))
        cv.drawString('NO SUNSET', -70, 20, f, paint(INKD))
        cv.restore()

# ---------- C: by design ----------
def s_design(cv, t):
    s_three(cv, 5.3)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', 0.35 * ease_out(prog(t, 0, 0.3))))
    stamp(cv, 'BY DESIGN', W / 2, 720, 0.25, t, 150, RUST, -9)

# ---------- D: the book ----------
def s_book(cv, t):
    paper_bg(cv)
    glow(cv, W / 2, 700, 600, '#ffcf6b', 0.3)
    # a former casino boss behind the book
    up = ease_out(prog(t, 1.2, 1.9))
    if up > 0:
        mascot(cv, W / 2 + 260, 560 + 180 * (1 - up), 0.72, a=up, color='#2a1a12')
        cv.save(); cv.translate(W / 2 + 330, 760)
        cig = P(); cig.addRect(skia.Rect(0, 0, 90, 14))
        cv.restore()
    # book
    op = ease_in_out(prog(t, 2.6, 3.4))
    bx, by = W / 2 - 40, 830
    cv.save(); cv.translate(bx, by); cv.rotate(-4)
    bw, bh = 520, 660
    cut(cv, rect_path(-bw / 2, -bh / 2, bw / 2, bh / 2), '#1d3b2c', 14, 20, 0.5)  # back cover
    pages = rect_path(-bw / 2 + 16, -bh / 2 + 14, bw / 2 - 10, bh / 2 - 12)
    cv.drawPath(pages, paint(PAPER))
    for k in range(14):
        cv.drawLine(-bw / 2 + 60, -bh / 2 + 90 + k * 38, bw / 2 - 60 - (90 if k % 5 == 4 else 0), -bh / 2 + 90 + k * 38,
                    paint('#6b5a44', 0.55 * op, 'stroke', 7))
    # front cover hinged on the left edge
    sx = math.cos(op * math.pi)
    cv.save(); cv.translate(-bw / 2, 0); cv.scale(sx, 1)
    cover = rect_path(0, -bh / 2, bw, bh / 2)
    cv.drawPath(cover, paint('#24503a' if sx > 0 else '#183526'))
    if sx > 0.15:
        cv.drawRect(skia.Rect(30, -bh / 2 + 30, bw - 30, bh / 2 - 30), paint(AMBER, 0.9, 'stroke', 5))
        fb = font('Playfair-Black', 70)
        text_c(cv, 'DESIGNING', bw / 2, -60, fb, paint(AMBER))
        text_c(cv, 'CASINOS', bw / 2, 30, fb, paint(AMBER))
        cv.drawLine(bw / 2 - 90, 80, bw / 2 + 90, 80, paint(AMBER, 1, 'stroke', 4))
        cv.drawCircle(bw / 2, 170, 46, paint(AMBER, 0.9, 'stroke', 5))
        cv.drawLine(bw / 2 - 30, 170, bw / 2 + 30, 170, paint(AMBER, 0.9, 'stroke', 5))
    cv.restore()
    cv.restore()
    a = back_out(prog(t, 0.0, 0.45))
    if a > 0:
        label(cv, 'YEAR 2000', W / 2, 330, 64, RUST, PAPER, rot=-3, fname='Inter-Black', s=a)
    b = ease_out(prog(t, 1.4, 1.8))
    if b > 0:
        label(cv, 'EX CASINO BOSS', W / 2 + 230, 470, 34, INKD, PAPER, rot=3, a=b)
    ground(cv, 1255)

# ---------- E: blueprint rules ----------
MAZE = [  # wall segments on a 8x8 grid, (x1,y1,x2,y2)
    (0, 0, 8, 0), (0, 8, 8, 8), (0, 0, 0, 7), (8, 1, 8, 8),
    (1, 1, 5, 1), (6, 0, 6, 2), (1, 1, 1, 4), (2, 2, 7, 2), (7, 2, 7, 6), (2, 2, 2, 6),
    (3, 3, 6, 3), (3, 3, 3, 7), (4, 4, 6, 4), (6, 4, 6, 7), (1, 5, 1, 8), (4, 5, 4, 8),
    (5, 5, 5, 7), (2, 7, 3, 7), (7, 7, 8, 7), (0, 7, 1, 7)]
PATH = [(7.5, 0.5), (6.5, 0.5)]  # filled below
WANDER = [(0.5, 7.5), (0.5, 4.5), (1.5, 4.5), (1.5, 1.5), (5.5, 1.5), (5.5, 0.5), (7.5, 0.5),
          (7.5, 1.5), (6.5, 1.5)]

def s_rules(cv, t):
    paper_bg(cv)
    blueprint_card(cv, 1.2)
    lf = font('Mono-Bold', 34)
    hdr = ease_out(prog(t, 0, 0.3))
    text_c(cv, 'THE RULE BOOK', W / 2, 330, font('Mono-Bold', 52), paint(BP_HI, hdr))
    # stage 1: low ceiling section view
    s1 = 1 - prog(t, 1.8, 1.95)
    if s1 > 0 and t > 0.5:
        a = ease_out(prog(t, 0.55, 0.8)) * s1
        lp = paint(BP_LINE, a, 'stroke', 5)
        cv.drawLine(180, 1020, W - 180, 1020, lp)
        drop = ease_in_out(prog(t, 0.75, 1.5))
        cy = 480 + 260 * drop
        cv.drawLine(180, cy, W - 180, cy, lp)
        for x in (180, W - 180):
            cv.drawLine(x, cy, x, 1020, lp)
        # little figure
        cv.save(); cv.translate(W / 2, 1020)
        cv.drawCircle(0, -150, 24, lp); cv.drawLine(0, -126, 0, -50, lp)
        cv.drawLine(0, -50, -26, 0, lp); cv.drawLine(0, -50, 26, 0, lp); cv.drawLine(-30, -100, 30, -100, lp)
        cv.restore()
        for x in (330, W - 330):
            cv.drawLine(x, cy - 90, x, cy - 10, paint(BP_HI, a, 'stroke', 4))
            ar = P(); ar.moveTo(x - 16, cy - 30); ar.lineTo(x, cy - 6); ar.lineTo(x + 16, cy - 30)
            cv.drawPath(ar, paint(BP_HI, a, 'stroke', 4))
        cv.drawString('RULE 1: LOW CEILINGS', 180, 410, lf, paint(BP_HI, a))
    # stage 2 + 3: maze then machines
    m = ease_out(prog(t, 1.9, 2.15))
    if m > 0:
        ox, oy, cs = 180, 440, 90
        lp = paint(BP_LINE, m, 'stroke', 6)
        drawn = prog(t, 1.9, 2.5)
        for i, (x1, y1, x2, y2) in enumerate(MAZE):
            k = clamp(drawn * len(MAZE) - i)
            if k <= 0: continue
            cv.drawLine(ox + x1 * cs, oy + y1 * cs, ox + (x1 + (x2 - x1) * k) * cs, oy + (y1 + (y2 - y1) * k) * cs, lp)
        # wandering dot
        w = clamp((t - 2.1) / 2.6) * (len(WANDER) - 1)
        i = min(int(w), len(WANDER) - 2); f = w - i
        x = WANDER[i][0] + (WANDER[i + 1][0] - WANDER[i][0]) * f
        y = WANDER[i][1] + (WANDER[i + 1][1] - WANDER[i][1]) * f
        cv.drawCircle(ox + x * cs, oy + y * cs, 18, paint(BP_HI, m))
        if t < 2.55: cv.drawString('RULE 2: MAZE PATHS', 180, 410, lf, paint(BP_HI, m))
        # machines pop along walls
        mc = prog(t, 2.55, 3.6)
        spots = [(1.5, 0.5), (3.5, 0.5), (2.5, 1.5), (4.5, 2.5), (6.5, 3.5), (2.5, 3.5), (5.5, 5.5),
                 (3.5, 5.5), (0.5, 2.5), (6.5, 6.5), (2.5, 6.5), (7.5, 4.5)]
        for j, (sx, sy) in enumerate(spots):
            q = back_out(clamp(mc * len(spots) - j), 2.5)
            if q <= 0: continue
            cx, cy = ox + sx * cs, oy + sy * cs
            cv.save(); cv.translate(cx, cy); cv.scale(q, q)
            cv.drawRoundRect(skia.Rect(-26, -32, 26, 32), 8, 8, paint(BP_HI))
            for k in range(3):
                cv.drawRect(skia.Rect(-20 + k * 14, -16, -10 + k * 14, 4), paint(BP))
            cv.restore()
        if mc > 0:
            cv.drawString('RULE 3: MACHINES EVERYWHERE', 180, 410, lf, paint(BP_HI, ease_out(mc * 3)))
    ground(cv, 1262)

BP = '#16477a'

# ---------- F: cash becomes chips ----------
def bill(cv, x, y, rot, sx=1.0, a=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sx, 1)
    cut(cv, rect_path(-170, -78, 170, 78), '#7fa36a', 6, 9, 0.4 * a)
    cv.drawRect(skia.Rect(-155, -64, 155, 64), paint('#3f6b38', a, 'stroke', 4))
    cv.drawCircle(0, 0, 44, paint('#5d8a52', a))
    f = font('Inter-Black', 40)
    cv.drawString('100', -150, -20, f, paint('#2c4d27', a)); cv.drawString('100', 72, 50, f, paint('#2c4d27', a))
    cv.restore()

def chip_face(cv, x, y, r, col, rot=0, sx=1.0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sx, 1)
    cut(cv, circ_path(0, 0, r), col, 6, 9, 0.45)
    for k in range(8):
        a = math.radians(k * 45)
        cv.drawRect(skia.Rect(-9, -r, 9, -r + 18), paint(PAPER)) if False else None
        cv.drawLine(math.cos(a) * r * 0.78, math.sin(a) * r * 0.78, math.cos(a) * r * 0.98, math.sin(a) * r * 0.98,
                    paint(PAPER, 1, 'stroke', 14))
    cv.drawCircle(0, 0, r * 0.55, paint(PAPER, 1, 'stroke', 4))
    cv.restore()

BILLS = [(W / 2 - 230, 560, -12), (W / 2 + 200, 520, 9), (W / 2 - 40, 760, 4), (W / 2 + 250, 860, -7),
         (W / 2 - 260, 920, 14), (W / 2 + 20, 1050, -4)]
CHIPC = [RUST, INKD, GREEN, '#1d5fa8', RUST, BROWN]

def s_chips(cv, t):
    paper_bg(cv)
    glow(cv, W / 2, 780, 600, '#ffcf6b', 0.25)
    for i, (x, y, r) in enumerate(BILLS):
        drop = ease_out(prog(t, 0.05 * i, 0.05 * i + 0.4))
        if drop <= 0: continue
        yy = y - 700 * (1 - drop)
        fl = prog(t, 2.1 + i * 0.12, 2.45 + i * 0.12)
        if fl < 0.5:
            bill(cv, x, yy, r, math.cos(fl * math.pi))
        else:
            chip_face(cv, x, yy, 95, CHIPC[i], r, -math.cos(fl * math.pi))
    a = ease_out(prog(t, 0.2, 0.5)) * (1 - prog(t, 1.9, 2.1))
    if a > 0: label(cv, 'REAL CASH', W / 2, 330, 56, INKD, PAPER, rot=-3, fname='Inter-Black', a=a)
    b = ease_out(prog(t, 2.2, 2.5))
    if b > 0: label(cv, 'CHIPS', W / 2, 330, 64, RUST, PAPER, rot=-3, fname='Inter-Black', a=b, s=0.7 + 0.3 * back_out(b))
    c = ease_out(prog(t, 3.2, 3.6))
    if c > 0: label(cv, 'FEELS LIKE A GAME', W / 2, 1200, 40, INKD, '#ffcf5a', rot=2, a=c)
    ground(cv, 1262)

# ---------- G: the free drinks ----------
def glass(cv, x, y, s, tilt=0):
    cv.save(); cv.translate(x, y); cv.rotate(tilt); cv.scale(s, s)
    bowl = P(); bowl.moveTo(-150, -260); bowl.lineTo(150, -260); bowl.lineTo(0, -40); bowl.close()
    stem = P(); stem.addRect(skia.Rect(-10, -45, 10, 160)); stem.addOval(skia.Rect(-110, 150, 110, 190))
    cut(cv, stem, '#e9e2d0', 8, 12, 0.45)
    cut(cv, bowl, '#e9e2d0', 8, 12, 0.45)
    liq = P(); liq.moveTo(-118, -213); liq.lineTo(118, -213); liq.lineTo(0, -48); liq.close()
    cv.drawPath(liq, paint('#d6463a'))
    cv.drawCircle(70, -250, 26, paint('#2f7a3a'))
    cv.drawLine(70, -250, 120, -330, paint(SHADOW, 1, 'stroke', 6))
    cv.restore()

def s_drinks(cv, t):
    hall(cv, t)
    sway = ease_in_out(prog(t, 3.9, 5.2))
    wob = math.sin(t * 3.0) * 7 * sway
    cv.save(); cv.translate(W / 2, 700); cv.rotate(wob); cv.translate(-W / 2, -700)
    bar = rect_path(-40, 1080, W + 40, 1260); cut(cv, bar, '#4a2c1a', 0, -10, 0.4)
    glass(cv, W / 2 - 60, 900, 1.15, tilt=-4 + 6 * sway)
    # swinging price tag
    sw = math.sin(t * 4) * 10 * math.exp(-t * 0.5) if t < 1.6 else math.sin(t * 4) * 5 * math.exp(-(t - 1.6) * 0.6)
    fl = prog(t, 2.4, 2.7)
    cv.save(); cv.translate(W / 2 + 10, 640); cv.rotate(sw)
    cv.drawLine(0, 0, 40, 120, paint(SHADOW, 1, 'stroke', 4))
    cv.translate(40, 120); cv.rotate(-8); cv.scale(abs(math.cos(fl * math.pi)) if fl < 1 else 1, 1)
    tag = P(); tag.moveTo(0, 0); tag.lineTo(60, -40); tag.lineTo(440, -40); tag.lineTo(440, 120); tag.lineTo(60, 120); tag.close()
    cut(cv, tag, PAPER, 8, 12, 0.45)
    cv.drawCircle(40, 40, 10, paint(SHADOW))
    if fl < 0.5:
        cv.drawString('FREE', 105, 75, font('Inter-Black', 96), paint(GREEN))
        x = ease_out(prog(t, 1.15, 1.35))
        if x > 0: cv.drawLine(95, 50, 95 + 270 * x, 20, paint(RUST, 1, 'stroke', 16))
    else:
        cv.drawString('PAID BY', 100, 30, font('Inter-Black', 46), paint(RUST))
        cv.drawString('YOUR BETS', 100, 95, font('Inter-Black', 46), paint(RUST))
    cv.restore()
    cv.restore()
    # slower mind: woozy rings
    if sway > 0:
        for k in range(3):
            rr = 60 + ((t * 70 + k * 50) % 150)
            cv.drawCircle(W / 2 - 60, 560, rr, paint(PAPER, 0.5 * sway * (1 - rr / 210), 'stroke', 5))
        label(cv, 'SLOWER MIND', W / 2, 330, 48, INKD, '#ffcf5a', rot=-3, a=sway)
    ground(cv, 1255)

# ---------- H: the puppet ----------
def s_puppet(cv, t):
    paper_bg(cv, '#b8382c', '#5a1510')
    glow(cv, W / 2, 760, 600, '#ff8a5a', 0.25)
    # giant hand at top
    d = ease_out(prog(t, 0, 0.5))
    hy = 200 - 220 * (1 - d)
    hand = P(); hand.addRoundRect(skia.Rect(W / 2 - 230, hy - 220, W / 2 + 230, hy + 40), 60, 60)
    for k in range(4):
        fx = W / 2 - 190 + k * 125
        hand.addRoundRect(skia.Rect(fx, hy + 10, fx + 85, hy + 120 + (k % 2) * 25), 40, 40)
    cut(cv, hand, SHADOW, 10, 16, 0.5)
    bob = math.sin(t * 3) * 18
    gx, gy = W / 2, 760 + bob
    tips = [(W / 2 - 150, hy + 120), (W / 2 - 25, hy + 145), (W / 2 + 100, hy + 120), (W / 2 + 225, hy + 145)]
    ends = [(gx - 150, gy + 170), (gx - 60, gy - 120), (gx + 60, gy - 120), (gx + 150, gy + 170)]
    s = ease_out(prog(t, 0.3, 0.8))
    for (x1, y1), (x2, y2) in zip(tips, ends):
        cv.drawLine(x1, y1, x1 + (x2 - x1) * s, y1 + (y2 - y1) * s, paint(PAPER, 0.85, 'stroke', 3))
    mascot(cv, gx, gy - 60, 0.78)
    # chip in hand of the puppet
    chip_face(cv, gx + 200, gy + 260, 50, RUST, t * 120)
    a = back_out(prog(t, 0.1, 0.5))
    if a > 0: label(cv, 'ONE JOB', W / 2, 1180, 60, PAPER, RUST, rot=-3, fname='Inter-Black', s=a)
    ground(cv, 1262, '#2a0b08')

# ---------- I: the maths over time ----------
def s_maths(cv, t):
    paper_bg(cv)
    blueprint_card(cv, -1.2)
    ox, oy, cw, ch = 200, 1030, 700, 560
    a = ease_out(prog(t, 0, 0.3))
    ax = paint(BP_LINE, a, 'stroke', 5)
    cv.drawLine(ox, oy, ox + cw, oy, ax); cv.drawLine(ox, oy, ox, oy - ch, ax)
    lf = font('Mono-Bold', 32)
    cv.drawString('TIME', ox + cw - 80, oy + 50, lf, paint(BP_LINE, a))
    cv.save(); cv.translate(ox - 30, oy - ch / 2 + 170); cv.rotate(-90)
    cv.drawString('YOUR MONEY', 0, 0, lf, paint(BP_LINE, a)); cv.restore()
    rng = random.Random(4)
    pts, v = [], 0.62
    for i in range(61):
        pts.append(v); v += rng.uniform(-0.05, 0.05) - 0.0085
    k = prog(t, 0.3, 2.6)
    n = max(2, int(k * 60) + 1)
    pth = P()
    for i in range(n):
        x = ox + cw * i / 60; y = oy - ch * max(0.03, pts[i])
        pth.moveTo(x, y) if i == 0 else pth.lineTo(x, y)
    cv.drawPath(pth, paint(BP_HI, a, 'stroke', 7))
    tip = (ox + cw * (n - 1) / 60, oy - ch * max(0.03, pts[n - 1]))
    cv.drawCircle(*tip, 14, paint(BP_HI, a))
    # house edge line rising
    hs = P(); hs.moveTo(ox, oy - ch * 0.05)
    hs.lineTo(ox + cw * k, oy - ch * (0.05 + 0.85 * k))
    hp = paint('#ff8f80', a, 'stroke', 5); hp.setPathEffect(skia.DashPathEffect.Make([22, 14], 0))
    cv.drawPath(hs, hp)
    if k > 0.6:
        cv.drawString('HOUSE', ox + cw * k - 170, oy - ch * (0.05 + 0.85 * k) - 20, lf, paint('#ff8f80', ease_out((k - 0.6) * 4)))
    text_c(cv, 'THE LONGER YOU STAY', W / 2, 360, font('Mono-Bold', 44), paint(BP_HI, a))
    ground(cv, 1262)

# ---------- J: end card ----------
def hourglass(cv, x, y, s, sand):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    frame = P(); frame.addRect(skia.Rect(-170, -300, 170, -270)); frame.addRect(skia.Rect(-170, 270, 170, 300))
    frame.addRect(skia.Rect(-160, -270, -140, 270)); frame.addRect(skia.Rect(140, -270, 160, 270))
    cut(cv, frame, '#3a2418', 8, 12, 0.45)
    gl = P(); gl.moveTo(-120, -270); gl.lineTo(120, -270); gl.lineTo(14, 0); gl.lineTo(120, 270); gl.lineTo(-120, 270)
    gl.lineTo(-14, 0); gl.close()
    cv.drawPath(gl, paint('#ffffff', 0.35))
    top = P(); h = 220 * (1 - sand)
    top.moveTo(-120 * h / 270 - 14, -h); top.lineTo(120 * h / 270 + 14, -h); top.lineTo(14, 0); top.lineTo(-14, 0); top.close()
    if sand < 1: cv.drawPath(top, paint(AMBER))
    bot = P(); hb = 220 * sand
    bot.moveTo(-120, 270); bot.lineTo(120, 270); bot.lineTo(120 - 40 * sand, 270 - hb); bot.lineTo(-120 + 40 * sand, 270 - hb); bot.close()
    cv.drawPath(bot, paint(AMBER))
    if sand < 1: cv.drawLine(0, 0, 0, 270 - hb, paint(AMBER, 1, 'stroke', 6))
    cv.drawPath(gl, paint(INKD, 1, 'stroke', 6))
    cv.restore()

def s_end(cv, t):
    paper_bg(cv)
    glow(cv, W / 2, 760, 600, '#ffcf6b', 0.3)
    hourglass(cv, W / 2, 900, 0.88, clamp(t / 3.3))
    a = ease_out(prog(t, 0.0, 0.35))
    torn = ease_out(prog(t, 1.1, 1.4))
    cv.save(); cv.translate(W / 2 - 200, 300); cv.rotate(-6 - 10 * torn); cv.translate(0, 50 * torn)
    fL = font('Inter-Black', 110); w = fL.measureText('LUCK')
    cut(cv, rect_path(-w / 2 - 30, -100, w / 2 + 30, 30), PAPER, 8, 12, 0.45 * a)
    text_c(cv, 'LUCK', 0, 0, fL, paint(INKD, a * (1 - 0.5 * torn)))
    if torn > 0: cv.drawLine(-w / 2 - 20, -38, -w / 2 - 20 + (w + 40) * torn, -42, paint(RUST, 1, 'stroke', 18))
    cv.restore()
    m = prog(t, 2.45, 2.8)
    if m > 0:
        s = back_out(m, 2.2)
        fT = font('Playfair-Black', 170); wT = fT.measureText('TIME')
        cv.save(); cv.translate(W / 2 + 110, 500); cv.rotate(4); cv.scale(s, s)
        cut(cv, rect_path(-wT / 2 - 36, -150, wT / 2 + 36, 44), INKD, 12, 16, 0.5)
        text_c(cv, 'TIME', 0, 0, fT, paint('#ffcf5a'))
        cv.restore()
    ground(cv, 1255)
    b = ease_out(prog(t, 0.5, 1.0))
    text_c(cv, 'THE RIGGED GAME', W / 2, 1720, font('Mono-Bold', 34), paint(PAPER, 0.8 * b))

# ---------- timeline (scene starts sit a beat before each sentence) ----------
SCENES = [
    (0.00, 4.35, s_clock_hunt), (4.35, 8.39, s_three), (8.39, 10.32, s_design),
    (10.32, 15.64, s_book), (15.64, 20.44, s_rules), (20.44, 25.04, s_chips),
    (25.04, 30.56, s_drinks), (30.56, 33.85, s_puppet), (33.85, 36.89, s_maths),
    (36.89, DUR + 0.1, s_end),
]
XF = 0.3
CHUNKS = caption_chunks()
CAP_Y = 1440

def captions(cv, t):
    for c in CHUNKS:
        if c['start'] <= t < c['end']:
            words = c['words']
            f = font('Inter-Black', 84); sp = f.measureText(' ')
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
                    key = w.strip(",.?").lower()
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
    fb = font('Mono-Bold', 26); txt = 'THE RIGGED GAME  |  EP 02'; bw = fb.measureText(txt)
    cv.drawRoundRect(skia.Rect(W / 2 - bw / 2 - 22, 64, W / 2 + bw / 2 + 22, 108), 22, 22, paint(INKD, 0.75))
    text_c(cv, txt, W / 2, 95, fb, paint(PAPER, 0.9))
    captions(cv, t)
    if t > DUR - 0.25:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', (t - (DUR - 0.25)) / 0.25))

def main():
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    if sys.argv[1] == 'stills':
        os.makedirs('stills', exist_ok=True)
        for tt in [float(x) for x in sys.argv[2:]]:
            cv.clear(skia.ColorBLACK); frame(cv, tt)
            surf.makeImageSnapshot().save(f'stills/f_{tt:05.2f}.png', skia.kPNG)
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
