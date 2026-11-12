"""The Rigged Game EP02 (countdown cut): 5 tricks casinos use to keep you playing."""
import math, random, sys, subprocess, os, json
sys.path.insert(0, '/home/claude/ep2'); sys.path.insert(0, '/home/claude/jagger')
import skia
from render import (W, H, FPS, C, font, paint, text_c, glow, clamp, ease_out, ease_in_out, back_out, prog)
from styles import cut, man_path, paper_bg
from noir_ep import (rect_path, circ_path, ground, label, blueprint_card, PAPER, INKD, RUST, AMBER, BROWN,
                     SHADOW, BP_LINE, BP_HI)
import ep2 as E
from timing3 import caption_chunks, EMPHASIS

DUR = 51.0
SEG = [x[0] for x in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vo.segments.json')))]
GREEN = '#2f5a3a'; BP = '#16477a'

def remap(t, pts):
    """piecewise-linear time warp so an existing scene's beats land on the new voice"""
    if t <= pts[0][0]: return pts[0][1] + (t - pts[0][0])
    for (a, oa), (b, ob) in zip(pts, pts[1:]):
        if t <= b: return oa + (ob - oa) * (t - a) / (b - a)
    return pts[-1][1] + (t - pts[-1][0])

# ---------- hook ----------
def s_hook(cv, t):
    E.hall(cv, t)
    ground(cv, 1250)
    E.mascot(cv, 190, 830, 0.78)
    # five cut-out cards fan out, numbered 5..1, card 1 is face down
    cards = 5
    for i in range(cards):
        a = back_out(prog(t, 0.15 + i * 0.12, 0.45 + i * 0.12), 1.8)
        if a <= 0: continue
        n = 5 - i
        ang = -30 + i * 15
        cv.save(); cv.translate(W / 2 + 60, 1320); cv.rotate(ang * a); cv.translate(0, -640)
        cv.scale(a, a)
        r = rect_path(-95, -140, 95, 140)
        if n == 1:
            cut(cv, r, RUST, 8, 12, 0.5)
            cv.drawRect(skia.Rect(-85, -130, 85, 130), paint(PAPER, 0.9, 'stroke', 5))
            text_c(cv, '?', 0, 50, font('Playfair-Black', 170), paint(PAPER))
        else:
            cut(cv, r, PAPER, 8, 12, 0.5)
            text_c(cv, str(n), 0, 55, font('Playfair-Black', 170), paint(INKD))
        cv.restore()
    a = ease_out(prog(t, 0.0, 0.4))
    label(cv, '5 HIDDEN TRICKS', W / 2, 300, 66, INKD, '#ffcf5a', rot=-3, fname='Inter-Black', a=a)
    # open loop: number one is locked
    b = prog(t, SEG[1] - 0.1, SEG[1] + 0.2)
    if b > 0:
        E.stamp(cv, 'TOP SECRET', W / 2 + 150, 520, SEG[1] + 0.9, t, 84, RUST, -12)

# ---------- countdown number cards ----------
def number_card(n, sub):
    def scene(cv, t):
        paper_bg(cv, '#2a1c12', '#0e0805')
        glow(cv, W / 2, 760, 650, '#ffb84a', 0.28)
        # rays
        for k in range(18):
            a0 = math.radians(k * 20 + t * 12); a1 = a0 + math.radians(8)
            p = skia.Path(); p.moveTo(W / 2, 760)
            p.lineTo(W / 2 + math.cos(a0) * 1500, 760 + math.sin(a0) * 1500)
            p.lineTo(W / 2 + math.cos(a1) * 1500, 760 + math.sin(a1) * 1500); p.close()
            cv.drawPath(p, paint(AMBER, 0.06))
        flip = prog(t, 0.0, 0.35)
        sx = abs(math.cos((1 - ease_out(flip)) * math.pi / 2 * 2)) if flip < 1 else 1
        s = 0.8 + 0.2 * back_out(flip)
        cv.save(); cv.translate(W / 2, 760); cv.rotate(-3 + 2 * math.sin(t * 2)); cv.scale(sx * s, s)
        r = rect_path(-260, -360, 260, 360)
        cut(cv, r, RUST if n == 1 else PAPER, 14, 20, 0.55)
        cv.drawRect(skia.Rect(-230, -330, 230, 330), paint(PAPER if n == 1 else INKD, 0.9, 'stroke', 6))
        text_c(cv, str(n), 0, 150, font('Playfair-Black', 480), paint(PAPER if n == 1 else INKD))
        cv.restore()
        a = ease_out(prog(t, 0.2, 0.5))
        label(cv, sub, W / 2, 1240, 54, INKD if n != 1 else PAPER, '#ffcf5a' if n != 1 else RUST, rot=2,
              fname='Inter-Black', a=a)
        label(cv, f'TRICK #{n}', W / 2, 300, 46, RUST, PAPER, rot=-3, a=a)
    return scene

def s_secret(cv, t):
    """open loop pays off: 'but number one is the craziest'"""
    number_card(1, 'THE CRAZIEST')(cv, t)
    shake = math.sin(t * 40) * 6 * clamp(1 - abs(t - 1.0) / 0.6)
    if shake:
        cv.translate(shake, 0)

# ---------- trick 5: content (reuses EP02 cards) ----------
def s_t5(cv, t):
    E.s_three(cv, remap(t, [(0, 0), (0.95, 0.85), (2.18, 1.85), (4.8, 4.5)]))

# ---------- trick 4: the maze ----------
SPOTS = [(1.5, 0.5), (3.5, 0.5), (2.5, 1.5), (4.5, 2.5), (6.5, 3.5), (2.5, 3.5), (5.5, 5.5),
         (3.5, 5.5), (0.5, 2.5), (6.5, 6.5), (2.5, 6.5), (7.5, 4.5)]
LOOP = [(0.5, 7.5), (0.5, 4.5), (1.5, 4.5), (1.5, 1.5), (5.5, 1.5), (5.5, 0.5), (7.5, 0.5), (7.5, 1.5),
        (6.5, 1.5), (6.5, 3.5), (3.5, 3.5), (3.5, 6.5), (2.5, 6.5), (2.5, 4.5), (1.5, 4.5), (0.5, 4.5)]

def s_t4(cv, t):
    paper_bg(cv)
    blueprint_card(cv, 1.2)
    ox, oy, cs = 180, 440, 90
    m = ease_out(prog(t, 0.0, 0.3))
    lp = paint(BP_LINE, m, 'stroke', 6)
    drawn = prog(t, 0.0, 0.8)
    for i, (x1, y1, x2, y2) in enumerate(E.MAZE):
        k = clamp(drawn * len(E.MAZE) - i)
        if k <= 0: continue
        cv.drawLine(ox + x1 * cs, oy + y1 * cs, ox + (x1 + (x2 - x1) * k) * cs, oy + (y1 + (y2 - y1) * k) * cs, lp)
    lf = font('Mono-Bold', 36)
    t_exit, t_mach = SEG[7] - SEG[6], SEG[8] - SEG[6]
    # EXIT sign tucked in the far corner, flickering
    ex = ease_out(prog(t, t_exit - 0.1, t_exit + 0.2))
    if ex > 0:
        fl = 0.55 + 0.45 * (math.sin(t * 17) > -0.3)
        cv.drawRoundRect(skia.Rect(ox + 8 * cs - 120, oy + 8 * cs + 18, ox + 8 * cs, oy + 8 * cs + 66), 8, 8,
                         paint('#ff8f80', ex * fl))
        cv.drawString('EXIT', ox + 8 * cs - 104, oy + 8 * cs + 57, font('Inter-Black', 40), paint(BP, ex))
    # a visitor going round in circles
    w = (max(0, t - 0.5) * 2.6) % (len(LOOP) - 1)
    i = int(w); f = w - i
    x = LOOP[i][0] + (LOOP[i + 1][0] - LOOP[i][0]) * f
    y = LOOP[i][1] + (LOOP[i + 1][1] - LOOP[i][1]) * f
    cv.drawCircle(ox + x * cs, oy + y * cs, 18, paint(BP_HI, m))
    mc = prog(t, t_mach - 0.1, t_mach + 0.9)
    for j, (sx, sy) in enumerate(SPOTS):
        q = back_out(clamp(mc * len(SPOTS) - j), 2.5)
        if q <= 0: continue
        cv.save(); cv.translate(ox + sx * cs, oy + sy * cs); cv.scale(q, q)
        cv.drawRoundRect(skia.Rect(-26, -32, 26, 32), 8, 8, paint(BP_HI))
        for kk in range(3):
            cv.drawRect(skia.Rect(-20 + kk * 14, -16, -10 + kk * 14, 4), paint(BP))
        cv.restore()
    hdr = 'MACHINES EVERYWHERE' if t > t_mach - 0.1 else ('WHERE IS THE EXIT?' if t > t_exit - 0.1 else 'THE MAZE')
    text_c(cv, hdr, W / 2, 380, font('Mono-Bold', 44), paint(BP_HI, m))
    ground(cv, 1262)

# ---------- trick 3 / trick 2 (reused, retimed) ----------
def s_t3(cv, t):
    E.s_chips(cv, remap(t, [(0, 0), (0.7, 2.05), (1.7, 3.1), (5.2, 6.6)]))

def s_t2(cv, t):
    E.s_drinks(cv, remap(t, [(0, 0), (0.85, 1.1), (1.25, 2.35), (3.0, 3.9), (4.4, 5.3)]))

# ---------- trick 1: loss disguised as a win ----------
SYMS = ['7', 'BAR', 'STAR', 'BELL']

def reel_symbol(cv, sym, x, y, sc=1.0):
    cv.save(); cv.translate(x, y); cv.scale(sc, sc)
    if sym == '7':
        text_c(cv, '7', 0, 45, font('Playfair-Black', 130), paint(RUST))
    elif sym == 'BAR':
        cv.drawRoundRect(skia.Rect(-62, -28, 62, 28), 8, 8, paint(INKD))
        text_c(cv, 'BAR', 0, 16, font('Inter-Black', 40), paint(PAPER))
    elif sym == 'STAR':
        p = skia.Path()
        for k in range(10):
            r = 60 if k % 2 == 0 else 26
            a = math.radians(-90 + k * 36)
            (p.moveTo if k == 0 else p.lineTo)(math.cos(a) * r, math.sin(a) * r)
        p.close(); cv.drawPath(p, paint(AMBER))
    else:
        p = skia.Path(); p.moveTo(-45, 35); p.quadTo(-45, -55, 0, -55); p.quadTo(45, -55, 45, 35); p.close()
        cv.drawPath(p, paint(AMBER)); cv.drawCircle(0, 45, 12, paint(AMBER))
    cv.restore()

CONF = [(random.Random(i).uniform(-1, 1), random.Random(i + 99).uniform(0.4, 1.0), i) for i in range(60)]

def s_t1(cv, t):
    T = lambda i: SEG[i] - SEG[16]  # local time of sentence i
    lost = prog(t, T(20) - 0.05, T(20) + 0.25)
    paper_bg(cv, '#3a1414' if lost > 0.5 else '#2a1c12', '#0e0805')
    party = clamp(prog(t, T(18) - 0.1, T(18) + 0.2)) * (1 - lost)
    glow(cv, W / 2, 640, 700, '#ffcf5a' if lost < 0.5 else '#ff5a4a', 0.25 + 0.25 * party)
    # cabinet
    cab = skia.Path(); cab.addRoundRect(skia.Rect(200, 270, W - 200, 1120), 60, 60)
    cut(cv, cab, '#7a1f19', 14, 20, 0.55)
    cv.drawRoundRect(skia.Rect(230, 300, W - 230, 1090), 46, 46, paint(AMBER, 0.85, 'stroke', 6))
    # marquee bulbs
    for k in range(13):
        bx = 270 + k * (W - 540) / 12
        on = party > 0 and (int(t * 10) + k) % 2 == 0
        cv.drawCircle(bx, 340, 14, paint('#fff1b0' if on else '#6b3a1a'))
        if on: glow(cv, bx, 340, 50, '#ffdf6b', 0.5 * party)
    # winner banner
    wb = back_out(prog(t, T(18) - 0.05, T(18) + 0.3), 2.2) * (1 - lost)
    if wb > 0:
        cv.save(); cv.translate(W / 2, 450); cv.rotate(-3 + math.sin(t * 9) * 2 * party); cv.scale(wb, wb)
        f = font('Inter-Black', 110); w = f.measureText('WINNER!')
        cut(cv, rect_path(-w / 2 - 30, -100, w / 2 + 30, 30), '#ffcf5a', 8, 12, 0.5)
        text_c(cv, 'WINNER!', 0, 0, f, paint(INKD))
        cv.restore()
    # reels window
    win = skia.Rect(270, 520, W - 270, 780)
    cv.drawRect(win, paint(PAPER))
    spin_end = [T(17) + 0.0, T(17) + 0.25, T(17) + 0.5]
    final = ['7', '7', 'BAR']
    cv.save(); cv.clipRect(win)
    rw = win.width() / 3
    for r in range(3):
        cx = win.left() + rw * (r + 0.5)
        if 0.2 < t < spin_end[r]:
            off = (t * 9 + r) % 1.0
            for k in range(-1, 3):
                reel_symbol(cv, SYMS[(int(t * 9) + k + r) % 4], cx, 650 + (k - off) * 170, 0.9)
        else:
            reel_symbol(cv, final[r] if t >= spin_end[r] else SYMS[r], cx, 650)
        if r: cv.drawLine(win.left() + rw * r, 520, win.left() + rw * r, 780, paint(INKD, 0.4, 'stroke', 3))
    cv.restore()
    cv.drawRect(win, paint(INKD, 1, 'stroke', 8))
    # coin slot + coin
    cv.drawRoundRect(skia.Rect(W / 2 - 60, 840, W / 2 + 60, 858), 8, 8, paint(SHADOW))
    cd = prog(t, 0.05, 0.45)
    if 0 < cd < 1:
        cy = 700 + 150 * ease_in_out(cd)
        cv.drawCircle(W / 2, cy - 120, 40, paint(AMBER)); cv.drawCircle(W / 2, cy - 120, 30, paint('#c9922a', 1, 'stroke', 4))
    # ledger card
    led = rect_path(300, 900, W - 300, 1080)
    cut(cv, led, PAPER, 8, 12, 0.5)
    lf = font('Mono-Bold', 44)
    cv.drawString('BET', 340, 960, lf, paint(INKD)); cv.drawString('$1.00', W - 480, 960, lf, paint(INKD))
    if t > spin_end[2]:
        cv.drawString('WON', 340, 1030, lf, paint(GREEN)); cv.drawString('$0.50', W - 480, 1030, lf, paint(GREEN))
    # music notes
    if party > 0:
        for k in range(6):
            ph = (t * 0.6 + k / 6) % 1
            nx = 160 + (k % 3) * 380 + math.sin(t * 3 + k) * 30
            ny = 1100 - ph * 900
            cv.save(); cv.translate(nx, ny)
            cv.drawCircle(0, 0, 18, paint(PAPER, party * (1 - ph)))
            cv.drawLine(16, 0, 16, -70, paint(PAPER, party * (1 - ph), 'stroke', 6))
            cv.restore()
        for dx, sp, i in CONF:
            ph = ((t - T(18)) * sp * 0.7 + i * 0.017) % 1
            cv.drawRect(skia.Rect(W / 2 + dx * 520, 200 + ph * 1000, W / 2 + dx * 520 + 14, 200 + ph * 1000 + 22),
                        paint([RUST, AMBER, PAPER, GREEN][i % 4], party))
    # the truth
    if lost > 0:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', 0.35 * lost))
        E.stamp(cv, '-$0.50', W / 2, 700, T(20) + 0.15, t, 170, RUST, -8)
    mk = prog(t, T(21) - 0.05, T(21) + 0.3)
    if mk > 0:
        # masquerade mask over the loss
        a = ease_out(mk)
        cv.save(); cv.translate(W / 2, 560 - 120 * (1 - a)); cv.scale(a, a)
        p = skia.Path()
        p.moveTo(-330, -20); p.cubicTo(-300, -110, -120, -90, 0, -30); p.cubicTo(120, -90, 300, -110, 330, -20)
        p.cubicTo(300, 90, 120, 90, 0, 30); p.cubicTo(-120, 90, -300, 90, -330, -20); p.close()
        p.addOval(skia.Rect(-230, -40, -90, 30)); p.addOval(skia.Rect(90, -40, 230, 30))
        p.setFillType(skia.PathFillType.kEvenOdd)
        cut(cv, p, AMBER, 10, 14, 0.55)
        cv.restore()
        label(cv, 'LOSS DISGUISED AS A WIN', W / 2, 1220, 50, '#ffcf5a', INKD, rot=-2, fname='Inter-Black', a=a)
    ground(cv, 1262, '#120707')

# ---------- ending + outro ----------
def s_end(cv, t):
    E.s_end(cv, remap(t, [(0, 0), (1.2, 1.1), (2.75, 2.45), (6, 5.7)]))
    o = ease_in_out(prog(t, 3.05, 3.6))
    if o > 0:
        paper_bg(cv, '#2a1c12', '#0e0805') if o >= 1 else cv.drawRect(skia.Rect(0, 0, W, H), paint('#120a06', o))
        glow(cv, W / 2, 640, 600, '#ffb84a', 0.25 * o)
        s = 0.9 + 0.1 * ease_out(o)
        cv.save(); cv.translate(W / 2, 700); cv.scale(s, s)
        E.mascot(cv, 0, -420, 0.6, a=o, color='#000000')
        fb = font('Playfair-Black', 120)
        text_c(cv, 'THE RIGGED', 0, 230, fb, paint(PAPER, o))
        text_c(cv, 'GAME', 0, 360, fb, paint('#ffcf5a', o))
        cv.restore()
        b = ease_out(prog(t, 3.5, 3.9))
        label(cv, 'FOLLOW FOR MORE CASINO SECRETS', W / 2, 1290, 40, RUST, PAPER, rot=-2, a=b)

# ---------- timeline ----------
def at(i, d=0.1): return SEG[i] - d
SCENES = [
    (0.0, at(2), s_hook),
    (at(2), at(3), number_card(5, 'NO CLOCKS')), (at(3), at(5), s_t5),
    (at(5), at(6), number_card(4, 'THE MAZE')), (at(6), at(9), s_t4),
    (at(9), at(10), number_card(3, 'CHIPS')), (at(10), at(12), s_t3),
    (at(12), at(13), number_card(2, 'FREE DRINKS')), (at(13), at(15), s_t2),
    (at(15), at(16), s_secret), (at(16), at(22), s_t1),
    (at(22), DUR + 0.1, s_end),
]
XF = 0.22
CHUNKS = caption_chunks()

def progress(cv, t):
    if t < SEG[2] - 0.2 or t > SEG[22]: return
    done = sum(1 for i in (2, 5, 9, 12, 15) if t >= SEG[i] - 0.05)
    for k in range(5):
        x = W / 2 - 2 * 46 + k * 46
        on = k < done
        pop = back_out(clamp((t - (SEG[(2, 5, 9, 12, 15)[k]] - 0.05)) / 0.25), 2.5) if on else 1
        cv.drawCircle(x, 150, 15 * pop if on else 13, paint(RUST if k == 4 and on else '#ffcf5a') if on else paint(PAPER, 0.6, 'stroke', 3))

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
    progress(cv, t)
    E.CHUNKS = CHUNKS
    E.EMPHASIS.clear(); E.EMPHASIS.update(EMPHASIS)
    E.captions(cv, t)
    if t > DUR - 0.45:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', (t - (DUR - 0.45)) / 0.45))

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
