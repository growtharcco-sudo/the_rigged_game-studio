"""spec.json -> voice -> video -> cover -> queue/<id>/

Usage:
  python pipeline/make_reel.py specs/<id>.json --sheet   # ONE check image: frame 0 + the end of every scene + cover
  python pipeline/make_reel.py specs/<id>.json           # full render into queue/<id>/
"""
import json, os, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
EM_DASH = '—'
FORBIDDEN = ['promo code', 'sign up', 'signup bonus', 'deposit bonus', 'free spins', 'how to win', 'guaranteed win',
             'guaranteed profit', 'sure win', 'easy money', 'bet now', 'play now', 'download the app', 'use my link',
             'stake.com', '1xbet', 'betway', 'parimatch', 'dafabet', 'fairplay', 'mostbet', 'dream11', 'mpl ', 'rummy',
             'bet365', 'draftkings', 'fanduel']


def check_spec(spec):
    """hard rules of the channel. Fails loudly instead of building something we cannot post"""
    errs = []
    post = spec.get('post', {})
    for k in ('instagram_caption', 'youtube_title', 'youtube_description'):
        if not post.get(k): errs.append(f'post.{k} is missing')
    every = json.dumps(spec, ensure_ascii=False)
    if EM_DASH in every: errs.append('em dash found (channel rule: no em dashes)')
    ig = post.get('instagram_caption', '')
    tags = [w for w in ig.split() if w.startswith('#')]
    if len(tags) != 5: errs.append(f'Instagram caption needs exactly 5 hashtags, has {len(tags)}')
    if '#theriggedgame' not in [t.lower() for t in tags]: errs.append('Instagram caption must include #theriggedgame')
    for need in ('Education only', '18+'):
        if need not in ig: errs.append(f'Instagram caption must say {need!r}')
        if need not in post.get('youtube_description', ''): errs.append(f'YouTube description must say {need!r}')
    if len(post.get('youtube_title', '')) > 100: errs.append('YouTube title over 100 characters')
    if not spec.get('sources'): errs.append('spec.sources is empty: every fact needs a source')
    if spec.get('voice', 'am_liam') != 'am_liam': errs.append('channel voice is am_liam')
    low = every.lower()
    for bad in FORBIDDEN:
        if bad in low: errs.append(f'forbidden (promotion / betting brand): {bad.strip()!r}')
    if 'http' in ig: errs.append('no links in the Instagram caption')
    if errs: raise SystemExit('SPEC CHECK FAILED:\n- ' + '\n- '.join(errs))


def sheet(spec, tl, out_dir):
    """one image: frame 0, the last moment of every scene, the outro, and the cover, tiled at 360x640"""
    import skia, noir
    ts = [0.0]
    for i, sc in enumerate(tl.scenes):
        end = tl.scenes[i + 1]['start'] - 0.3 if i + 1 < len(tl.scenes) else tl.voice_end - 0.05
        ts.append(round(max(end, sc['start'] + 0.2), 2))
    if any(e['type'] == 'outro' for e in tl.scenes[-1]['els']): ts.append(round(tl.dur - 0.6, 2))
    paths = []
    for t in ts:
        p = os.path.join(out_dir, f'still_{t:06.2f}.png'); noir.still(tl, t, p); paths.append(p)
    cov = os.path.join(out_dir, 'cover.png'); noir.cover(spec, cov); paths.append(cov)
    cols = 5; rows = (len(paths) + cols - 1) // cols
    surf = skia.Surface(360 * cols, 640 * rows + 40); cv = surf.getCanvas(); cv.clear(skia.Color(20, 14, 10))
    f = noir.font('Mono-Bold', 22)
    for i, p in enumerate(paths):
        im = skia.Image.open(p); x, y = (i % cols) * 360, (i // cols) * 640
        cv.drawImageRect(im, skia.Rect(x, y, x + 360, y + 640), skia.SamplingOptions(skia.FilterMode.kLinear))
        tag = 'cover' if p == cov else f'{ts[i]:.1f}s'
        cv.drawRect(skia.Rect(x, y + 610, x + 90, y + 640), noir.paint('#000000', 0.7))
        cv.drawString(tag, x + 8, y + 632, f, noir.paint('#ffffff'))
    out = os.path.join(out_dir, 'sheet.png'); surf.makeImageSnapshot().save(out, skia.kPNG)
    for p in paths[:-1]: os.remove(p)
    return out, ts


def main():
    path = sys.argv[1]
    spec = json.load(open(path))
    check_spec(spec)
    import voice, noir
    out = os.path.join(ROOT, 'queue', spec['id']); os.makedirs(out, exist_ok=True)
    wav = os.path.join(out, 'voice.wav')
    _, times, words, total = voice.synth(spec['phrases'], wav, spec.get('voice', 'am_liam'), spec.get('speed', 1.0))
    timing = os.path.join(out, 'timing.json')
    json.dump({'times': times, 'words': words, 'total': total}, open(timing, 'w'), indent=1)
    tl = noir.Timeline(json.load(open(path)), times, words, total)
    if '--sheet' in sys.argv:
        p, ts = sheet(spec, tl, out)
        print('check sheet:', os.path.relpath(p, ROOT), f'({tl.dur:.1f}s, frames at {", ".join(f"{t:.1f}" for t in ts)})')
        return
    mp4 = os.path.join(out, 'video.mp4')
    noir.render_video(os.path.abspath(path), timing, wav, mp4, tl.dur)
    noir.cover(spec, os.path.join(out, 'cover.png'))
    os.remove(wav)
    shutil.copy(path, os.path.join(out, 'spec.json'))
    json.dump(spec['post'], open(os.path.join(out, 'post.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'ready: {os.path.relpath(mp4, ROOT)} ({tl.dur:.1f}s)')


if __name__ == '__main__':
    main()
