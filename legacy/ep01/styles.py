import math, random, sys, subprocess
import skia
from render import (W, H, FPS, C, font, paint, text_c, glow, clamp, ease_out, ease_in_out,
                    back_out, prog, wheel, man, casino, GOLD, CREAM, RED, INK)
from timing import caption_chunks, EMPHASIS

R = random.Random(5)

# ---------------- shared bits ----------------
def cap(cv, words, y=1440, fill='#ffffff', accent=GOLD, stroke='#000000', fname='Inter-Black', size=84, box=None):
    f = font(fname, size)
    sp = f.measureText(' ')
    ws = [w.upper() for w in words]
    lines, cur, cw = [], [], 0
    for w in ws:
        wd = f.measureText(w)
        if cur and cw + sp + wd > 900:
            lines.append(cur); cur, cw = [], 0
        cur.append(w); cw += (sp if cw else 0) + wd
    lines.append(cur)
    lh = size * 1.12
    y0 = y - (len(lines) - 1) * lh / 2
    for li, ln in enumerate(lines):
        tot = sum(f.measureText(w) for w in ln) + sp * (len(ln) - 1)
        x = W / 2 - tot / 2
        yy = y0 + li * lh
        if box:
            cv.drawRoundRect(skia.Rect(x - 36, yy - size * 0.95, x + tot + 36, yy + size * 0.35), 14, 14, paint(box))
        for w in ln:
            k = w.strip(',.').lower()
            if stroke:
                cv.drawString(w, x, yy, f, paint(stroke, 1, 'stroke', 14))
            cv.drawString(w, x, yy, f, paint(accent if k in EMPHASIS else fill))
            x += f.measureText(w) + sp

def cut(cv, path, color, dx=10, dy=14, sh=0.45):
    """paper cut-out layer: soft drop shadow then flat fill"""
    s = skia.Path(path); s.offset(dx, dy)
    cv.drawPath(s, paint('#000000', sh, blur=9))
    cv.drawPath(path, paint(color))

def casino_sil(cx, base, sc):
    p = skia.Path()
    def rect(x, y, w, h): p.addRect(skia.Rect(cx + x * sc, base + y * sc, cx + (x + w) * sc, base + (y + h) * sc))
    rect(-430, -300, 860, 300)
    for tx in (-430, 330):
        rect(tx, -470, 100, 470)
        q = skia.Path(); q.moveTo(cx + tx * sc, base - 470 * sc)
        q.quadTo(cx + (tx + 50) * sc, base - 600 * sc, cx + (tx + 100) * sc, base - 470 * sc); q.close()
        p.addPath(q)
        rect(tx + 47, -650, 6, 80)
    rect(-180, -380, 360, 380)
    q = skia.Path(); q.moveTo(cx - 180 * sc, base - 380 * sc)
    q.cubicTo(cx - 170 * sc, base - 560 * sc, cx + 170 * sc, base - 560 * sc, cx + 180 * sc, base - 380 * sc); q.close()
    p.addPath(q)
    p.setFillType(skia.PathFillType.kWinding)
    return p

def casino_windows(cv, cx, base, sc, color, a=1.0):
    for wx in list(range(-400, -200, 70)) + list(range(220, 400, 70)) + [-130, -40, 50]:
        top = -250 if abs(wx) > 180 else -330
        hh = 170 if abs(wx) > 180 else 240
        cv.drawRoundRect(skia.Rect(cx + (wx + 10) * sc, base + top * sc, cx + (wx + 54) * sc, base + (top + hh) * sc),
                         22 * sc, 22 * sc, paint(color, a))

def man_path(x, y, s):
    p = skia.Path()
    p.moveTo(x - 150 * s, y + 520 * s)
    p.cubicTo(x - 160 * s, y + 250 * s, x - 120 * s, y + 140 * s, x - 60 * s, y + 120 * s)
    p.lineTo(x + 60 * s, y + 120 * s)
    p.cubicTo(x + 120 * s, y + 140 * s, x + 160 * s, y + 250 * s, x + 150 * s, y + 520 * s); p.close()
    p.addCircle(x, y + 60 * s, 62 * s)
    p.addRect(skia.Rect(x - 95 * s, y + 5 * s, x + 95 * s, y + 25 * s))
    p.addRect(skia.Rect(x - 58 * s, y - 120 * s, x + 58 * s, y + 10 * s))
    # cane
    p.addRect(skia.Rect(x + 175 * s, y + 250 * s, x + 187 * s, y + 520 * s))
    p.setFillType(skia.PathFillType.kWinding)
    return p

def palm(x, base, s):
    p = skia.Path()
    p.moveTo(x - 10 * s, base); p.quadTo(x + 30 * s, base - 250 * s, x + 10 * s, base - 480 * s)
    p.lineTo(x + 26 * s, base - 480 * s); p.quadTo(x + 48 * s, base - 250 * s, x + 12 * s, base); p.close()
    for ang in (-160, -120, -60, -20, -90):
        a = math.radians(ang)
        tipx, tipy = x + 18 * s + math.cos(a) * 190 * s, base - 480 * s + math.sin(a) * 110 * s + 60 * s
        q = skia.Path(); q.moveTo(x + 18 * s, base - 482 * s)
        q.quadTo((x + 18 * s + tipx) / 2, base - 560 * s, tipx, tipy)
        q.quadTo((x + 18 * s + tipx) / 2, base - 520 * s, x + 18 * s, base - 470 * s); q.close()
        p.addPath(q)
    return p

PAPER_FIBERS = [(R.uniform(0, W), R.uniform(0, H), R.uniform(30, 140), R.uniform(0, 3.14)) for _ in range(160)]

def paper_bg(cv, top='#efe2c4', bot='#d9c49b'):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([(0, 0), (0, H)], [C(top), C(bot)]))
    cv.drawRect(skia.Rect(0, 0, W, H), p)
    for x, y, l, a in PAPER_FIBERS:
        cv.drawLine(x, y, x + math.cos(a) * l, y + math.sin(a) * l, paint('#8a6a3a', 0.05, 'stroke', 2))
    v = skia.Paint()
    v.setShader(skia.GradientShader.MakeRadial((W / 2, H * 0.45), H * 0.8,
                [skia.Color(0, 0, 0, 0), skia.Color(40, 20, 0, 0), skia.Color(40, 20, 0, 150)], [0, 0.5, 1]))
    cv.drawRect(skia.Rect(0, 0, W, H), v)

# ---------------- 1. NOIR PAPER CUTOUT ----------------
def noir(cv, t, cap_words=('IN', 'THE', '1800s,')):
    paper_bg(cv)
    cam = t  # parallax driver
    # red sun
    sx = W / 2 + 160 - cam * 8
    cut(cv, (lambda: (lambda p: (p.addCircle(sx, 620, 250), p)[1])(skia.Path()))(), '#b3261e', 6, 8, 0.3)
    # far layer: hills/city
    far = skia.Path(); far.moveTo(-100, 1000)
    for i in range(14):
        x = -100 + i * 100 - cam * 12
        far.lineTo(x, 900 - (60 if i % 3 else 140) - (i % 2) * 30)
        far.lineTo(x + 100, 900 - (60 if i % 3 else 140) - (i % 2) * 30)
    far.lineTo(W + 200, 1000); far.lineTo(W + 200, 1300); far.lineTo(-100, 1300); far.close()
    cut(cv, far, '#7a5a3a', 6, 8, 0.25)
    # mid layer: casino
    cx = W / 2 - cam * 22
    cs = casino_sil(cx, 1150, 0.95)
    cut(cv, cs, '#6b4630', 10, 14, 0.4)
    casino_windows(cv, cx, 1150, 0.95, '#e8b04a', 0.9)
    # ground
    g = skia.Path(); g.addRect(skia.Rect(-50, 1140, W + 50, H)); cut(cv, g, '#1a100b', 0, -8, 0.35)
    # front layer: palms + man
    cut(cv, palm(70 - cam * 45, 1250, 1.25), '#0d0806', 12, 16, 0.45)
    cut(cv, palm(W - 130 - cam * 45, 1270, 1.1), '#0d0806', 12, 16, 0.45)
    mx = 300 - cam * 60 + 90 * ease_out(clamp(t / 2.5))
    cut(cv, man_path(mx, 830, 0.82), '#050302', 14, 18, 0.5)
    # title cut-out label
    a = ease_out(prog(t, 0.1, 0.8))
    f = font('Playfair-Black', 190)
    s = back_out(prog(t, 0.1, 0.9))
    cv.save(); cv.translate(W / 2, 400); cv.rotate(-3); cv.scale(s, s)
    w = f.measureText('1800s')
    lab = skia.Path(); lab.addRect(skia.Rect(-w / 2 - 40, -175, w / 2 + 40, 50))
    cut(cv, lab, '#f6ecd4', 8, 12, 0.4 * a)
    text_c(cv, '1800s', 0, 0, f, paint('#1a100b', a))
    cv.restore()
    f2 = font('Mono-Bold', 40)
    cv.save(); cv.translate(W / 2, 520); cv.rotate(-3)
    lab2 = skia.Path(); lab2.addRect(skia.Rect(-210, -42, 210, 18)); cut(cv, lab2, '#b3261e', 6, 8, 0.35 * a)
    text_c(cv, 'MONTE CARLO', 0, 0, f2, paint('#f6ecd4', a))
    cv.restore()
    if cap_words:
        cap(cv, cap_words, fill='#f6ecd4', accent='#ffcf5a', stroke='#000000')

# ---------------- 2. DETECTIVE CASE FILE ----------------
def casefile(cv, t):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeLinear([(0, 0), (W, H)], [C('#4a2e1c'), C('#24150c')]))
    cv.drawRect(skia.Rect(0, 0, W, H), p)
    for i in range(0, H, 90):
        cv.drawLine(0, i + 20 * math.sin(i), W, i + 30, paint('#000000', 0.12, 'stroke', 3))
    glow(cv, W / 2, 700, 750, '#ffd28a', 0.22)
    # manila folder
    cv.save(); cv.rotate(2)
    fold = skia.Rect(90, 180, W - 70, 1260)
    cv.drawRoundRect(fold.makeOffset(10, 16), 14, 14, paint('#000000', 0.5, blur=14))
    cv.drawRoundRect(fold, 14, 14, paint('#d9b878'))
    cv.drawRoundRect(skia.Rect(90, 150, 400, 210), 12, 12, paint('#d9b878'))
    cv.drawString('CASE 001', 120, 196, font('Mono-Bold', 34), paint(INK))
    cv.restore()
    # newspaper clipping
    cv.save(); cv.translate(560, 330); cv.rotate(4)
    news = skia.Rect(0, 0, 420, 420)
    cv.drawRect(news.makeOffset(6, 10), paint('#000000', 0.4, blur=8))
    cv.drawRect(news, paint('#ece6d6'))
    cv.drawString('MONTE CARLO', 24, 62, font('Playfair-Black', 54), paint('#111111'))
    cv.drawString('WHEEL BEATEN!', 24, 118, font('Playfair-Bold', 44), paint('#111111'))
    for k in range(9):
        cv.drawLine(24, 160 + k * 26, 396 - (60 if k % 4 == 3 else 0), 160 + k * 26, paint('#555555', 0.6, 'stroke', 8))
    cv.restore()
    # polaroid with casino
    cv.save(); cv.translate(140, 560); cv.rotate(-6)
    pol = skia.Rect(0, 0, 470, 540)
    cv.drawRect(pol.makeOffset(8, 12), paint('#000000', 0.45, blur=10))
    cv.drawRect(pol, paint('#f7f4ec'))
    photo = skia.Rect(25, 25, 445, 425)
    cv.drawRect(photo, paint('#1b2a35'))
    cv.save(); cv.clipRect(photo)
    casino(cv, 235, 400, 0.42, 1.0)
    cv.restore()
    cv.drawString('Casino, 1800s', 60, 495, font('Playfair-Bold', 40), paint('#333333'))
    cv.restore()
    # pins + red string
    pins = [(380, 590), (780, 350), (760, 960)]
    for (x1, y1), (x2, y2) in zip(pins, pins[1:] + pins[:1]):
        pth = skia.Path(); pth.moveTo(x1, y1); pth.quadTo((x1 + x2) / 2, (y1 + y2) / 2 + 40, x2, y2)
        cv.drawPath(pth, paint('#c0241c', 1, 'stroke', 5))
    for x, y in pins:
        cv.drawCircle(x + 3, y + 5, 14, paint('#000000', 0.4, blur=3)); cv.drawCircle(x, y, 14, paint('#d83a2a'))
    # sticky note
    cv.save(); cv.translate(640, 850); cv.rotate(-5)
    cv.drawRect(skia.Rect(6, 10, 286, 290), paint('#000000', 0.35, blur=8))
    cv.drawRect(skia.Rect(0, 0, 280, 280), paint('#f4d35e'))
    cv.drawString('watched', 30, 110, font('Playfair-Bold', 52), paint(INK))
    cv.drawString('30 days?', 30, 190, font('Playfair-Bold', 52), paint('#c0241c'))
    cv.restore()
    # stamp
    cv.save(); cv.translate(150, 1215); cv.rotate(-8)
    f = font('Inter-Black', 80); w = f.measureText('EXPOSED')
    cv.drawRoundRect(skia.Rect(-20, -78, w + 20, 22), 10, 10, paint('#c0241c', 0.85, 'stroke', 8))
    cv.drawString('EXPOSED', 0, 0, f, paint('#c0241c', 0.85))
    cv.restore()
    cap(cv, ['IN', 'THE', '1800s,'], fname='Mono-Bold', size=80, fill='#111111', accent='#c0241c', stroke=None, box='#f7f4ec', y=1460)

# ---------------- 3. BLUEPRINT ----------------
def blueprint(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0d3b6e'))
    glow(cv, W / 2, 700, 900, '#2f7fd0', 0.35)
    for x in range(0, W, 40):
        cv.drawLine(x, 0, x, H, paint('#ffffff', 0.10 if x % 200 else 0.22, 'stroke', 1.5))
    for y in range(0, H, 40):
        cv.drawLine(0, y, W, y, paint('#ffffff', 0.10 if y % 200 else 0.22, 'stroke', 1.5))
    line = paint('#eaf4ff', 0.95, 'stroke', 4)
    # casino outline
    cs = casino_sil(W / 2, 760, 0.62)
    cv.drawPath(cs, line)
    # wheel outline
    cx, cy, r = W / 2, 1060, 210
    for rr in (r, r * 0.85, r * 0.55, r * 0.2):
        cv.drawCircle(cx, cy, rr, line)
    for i in range(37):
        a = math.radians(i * 360 / 37)
        cv.drawLine(cx + math.cos(a) * r * 0.55, cy + math.sin(a) * r * 0.55,
                    cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85, paint('#eaf4ff', 0.8, 'stroke', 2))
    # off-centre axis callout
    cv.drawCircle(cx + 18, cy - 10, 10, paint('#ffcf5a'))
    cv.drawLine(cx + 18, cy - 10, cx + 330, cy - 180, paint('#ffcf5a', 1, 'stroke', 3))
    f = font('Mono-Bold', 30)
    cv.drawString('AXIS OFF CENTRE?', cx + 160, cy - 200, f, paint('#ffcf5a'))
    # dimension line
    cv.drawLine(cx - r, cy + r + 50, cx + r, cy + r + 50, paint('#eaf4ff', 0.9, 'stroke', 2))
    for xx in (cx - r, cx + r):
        cv.drawLine(xx, cy + r + 30, xx, cy + r + 70, paint('#eaf4ff', 0.9, 'stroke', 2))
    text_c(cv, '37 POCKETS', cx, cy + r + 40, font('Mono-Bold', 26), paint('#eaf4ff'))
    # title block
    cv.drawRect(skia.Rect(80, 150, W - 80, 330), paint('#eaf4ff', 0.9, 'stroke', 3))
    cv.drawLine(80, 250, W - 80, 250, paint('#eaf4ff', 0.9, 'stroke', 2))
    cv.drawString('PLAN: MONTE CARLO', 110, 222, font('Mono-Bold', 58), paint('#eaf4ff'))
    cv.drawString('DWG 001   |   1800s   |   J. JAGGER', 110, 305, font('Mono-Bold', 30), paint('#9fc7f0'))
    cap(cv, ['IN', 'THE', '1800s,'], fname='Mono-Bold', size=86, fill='#eaf4ff', accent='#ffcf5a', stroke='#0a2a50')

# ---------------- 4. RETRO ART DECO POSTER ----------------
def deco(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0f3d3a'))
    cx, cy = W / 2, 900
    # sunburst
    for i in range(36):
        a0 = math.radians(i * 10); a1 = math.radians(i * 10 + 5)
        p = skia.Path(); p.moveTo(cx, cy)
        p.lineTo(cx + math.cos(a0) * 1800, cy + math.sin(a0) * 1800)
        p.lineTo(cx + math.cos(a1) * 1800, cy + math.sin(a1) * 1800); p.close()
        cv.drawPath(p, paint('#e2b84a', 0.16))
    cv.drawCircle(cx, cy, 330, paint('#e8743b'))
    for k in range(6):
        cv.drawRect(skia.Rect(cx - 340, cy + 60 + k * 45, cx + 340, cy + 80 + k * 45), paint('#0f3d3a'))
    # halftone dots bottom
    for y in range(1100, 1700, 26):
        for x in range(0, W + 26, 26):
            rr = 2 + 8 * clamp((y - 1100) / 600)
            cv.drawCircle(x + (13 if (y // 26) % 2 else 0), y, rr, paint('#0a2826'))
    cs = casino_sil(cx, 1180, 0.9)
    cv.drawPath(cs, paint('#16201f'))
    casino_windows(cv, cx, 1180, 0.9, '#e2b84a')
    # frame
    for inset, wdt in ((40, 6), (60, 2)):
        cv.drawRect(skia.Rect(inset, inset, W - inset, H - inset), paint('#e2b84a', 1, 'stroke', wdt))
    for (x, y) in ((40, 40), (W - 40, 40), (40, H - 40), (W - 40, H - 40)):
        cv.drawCircle(x, y, 18, paint('#e2b84a'))
    text_c(cv, 'MONTE', W / 2, 300, font('Playfair-Black', 190), paint('#f4ead2'))
    text_c(cv, 'CARLO', W / 2, 470, font('Playfair-Black', 190), paint('#e2b84a'))
    text_c(cv, 'THE 1800s', W / 2, 545, font('Mono-Bold', 40), paint('#f4ead2'))
    cap(cv, ['IN', 'THE', '1800s,'], size=84, fill='#f4ead2', accent='#e8743b', stroke='#0a2826')

def labeled(fn, label, num, t=1.6):
    surf = skia.Surface(W, H); cv = surf.getCanvas()
    fn(cv, t)
    # label banner
    cv.drawRect(skia.Rect(0, H - 220, W, H), paint('#000000', 0.82))
    text_c(cv, f'{num}. {label}', W / 2, H - 95, font('Inter-Black', 70), paint('#ffffff'))
    surf.makeImageSnapshot().save(f'styles/style_{num}.png', skia.kPNG)

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        labeled(noir, 'NOIR PAPER CUTOUT', 1)
        labeled(casefile, 'CASE FILE', 2)
        labeled(blueprint, 'BLUEPRINT', 3)
        labeled(deco, 'RETRO POSTER', 4)
    else:
        # 5.45 s noir sample with live captions
        chunks = [c for c in caption_chunks() if c['start'] < 5.45]
        surf = skia.Surface(W, H); cv = surf.getCanvas()
        ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba',
                               '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-ss', '0', '-t', '5.45', '-i', 'vo.mp3',
                               '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14',
                               '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                               '-movflags', '+faststart', 'styles/Noir sample.mp4'], stdin=subprocess.PIPE)
        for i in range(int(5.45 * FPS)):
            t = i / FPS
            cv.clear(skia.ColorBLACK)
            cur = [c for c in chunks if c['start'] <= t < c['end']]
            noir(cv, t, cap_words=None)
            if cur:
                c = cur[0]
                age = t - c['start']
                s = 0.85 + 0.15 * back_out(clamp(age / 0.18), 2.0)
                cv.save(); cv.translate(W / 2, 1440); cv.scale(s, s); cv.translate(-W / 2, -1440)
                cap(cv, [w[0] for w in c['words']], fill='#f6ecd4', accent='#ffcf5a')
                cv.restore()
            ff.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        ff.stdin.close(); ff.wait()
