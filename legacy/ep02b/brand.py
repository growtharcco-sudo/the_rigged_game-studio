"""Profile picture (1080x1080) and YouTube banner (2560x1440) for The Rigged Game."""
import sys, math
sys.path.insert(0, '/home/claude/ep2'); sys.path.insert(0, '/home/claude/jagger')
import skia
from render import C, font, paint, text_c, glow, wheel
from styles import cut, man_path, paper_bg
from noir_ep import rect_path, PAPER, INKD, RUST, AMBER

GOLD = '#ffcf5a'

def bg(cv, w, h):
    p = skia.Paint()
    p.setShader(skia.GradientShader.MakeRadial((w / 2, h * 0.45), max(w, h) * 0.75,
                [C('#3a2616'), C('#1a0f08'), C('#0b0604')], [0, 0.55, 1]))
    cv.drawRect(skia.Rect(0, 0, w, h), p)

def rays(cv, cx, cy, n=24, alpha=0.07):
    for k in range(n):
        a0 = math.radians(k * 360 / n); a1 = a0 + math.radians(360 / n / 2.2)
        p = skia.Path(); p.moveTo(cx, cy)
        p.lineTo(cx + math.cos(a0) * 3000, cy + math.sin(a0) * 3000)
        p.lineTo(cx + math.cos(a1) * 3000, cy + math.sin(a1) * 3000); p.close()
        cv.drawPath(p, paint(AMBER, alpha))

def emblem(cv, cx, cy, R):
    """roulette wheel behind the gambler's silhouette"""
    glow(cv, cx, cy, R * 1.6, '#ffb84a', 0.35)
    wheel(cv, cx, cy, R, rot=-6)
    s = R / 360
    disc = skia.Path(); disc.addCircle(cx, cy, R * 0.6)
    cut(cv, disc, '#efe2c4', 8 * s, 12 * s, 0.5)
    cv.save(); cv.clipPath(disc)
    cut(cv, man_path(cx, cy - R * 0.42, 0.62 * s), '#050302', 10 * s, 14 * s, 0.5)
    cv.restore()
    cv.drawCircle(cx, cy, R * 0.6, paint(GOLD, 1, 'stroke', 8 * s))

# ---------- profile picture ----------
W = H = 1080
surf = skia.Surface(W, H); cv = surf.getCanvas()
bg(cv, W, H); rays(cv, W / 2, H / 2)
emblem(cv, W / 2, H / 2 + 20, 360)
cv.drawCircle(W / 2, H / 2, 500, paint(GOLD, 0.9, 'stroke', 10))
surf.makeImageSnapshot().save('brand/profile_picture.png', skia.kPNG)

# ---------- YouTube banner (safe area: centre 1546x423) ----------
W, H = 2560, 1440
surf = skia.Surface(W, H); cv = surf.getCanvas()
bg(cv, W, H); rays(cv, W / 2, H / 2, 36, 0.05)
for x in (300, W - 300):
    cv.drawCircle(x, H / 2, 260, paint('#000000', 0.3))
    wheel(cv, x, H / 2, 230, rot=x / 10)
cv.save(); cv.translate(W / 2, H / 2)
f1 = font('Playfair-Black', 128)
text_c(cv, 'THE RIGGED GAME', 0, 10, f1, paint(PAPER))
tw = f1.measureText('THE RIGGED GAME')
cv.drawLine(-tw / 2, 50, tw / 2, 50, paint(GOLD, 1, 'stroke', 5))
f2 = font('Inter-Black', 52)
w2 = f2.measureText('HOW CASINOS REALLY WORK')
cut(cv, rect_path(-w2 / 2 - 34, 82, w2 / 2 + 34, 162), RUST, 8, 12, 0.5)
text_c(cv, 'HOW CASINOS REALLY WORK', 0, 142, f2, paint(PAPER))
cv.restore()
text_c(cv, 'CASINO SECRETS  |  REAL ODDS  |  GAMBLING HISTORY', W / 2, H / 2 - 160, font('Mono-Bold', 36), paint(GOLD, 0.9))
surf.makeImageSnapshot().save('brand/youtube_banner.png', skia.kPNG)
print('ok')
