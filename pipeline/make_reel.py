"""spec.json -> voice -> video -> cover -> queue/<id>/

Usage:
  python pipeline/make_reel.py specs/<id>.json --check   # channel rules only (captions, sources, math)
  python pipeline/make_reel.py specs/<id>.json --sheet   # ONE check image: frame 0 + the end of every scene + cover
  python pipeline/make_reel.py specs/<id>.json           # full render into queue/<id>/
"""
import datetime as dt, json, math, os, re, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
CHANNEL = json.load(open(os.path.join(ROOT, 'channel.json')))
EM_DASH, EN_DASH = '\u2014', '\u2013'
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
BRAND_TAG = CHANNEL['brand_tag']
SLOTS = CHANNEL['slots']
FORBIDDEN = ['promo code', 'sign up', 'signup bonus', 'deposit bonus', 'free spins', 'how to win', 'guaranteed win',
             'guaranteed profit', 'sure win', 'easy money', 'bet now', 'play now', 'download the app', 'use my link',
             'stake.com', '1xbet', 'betway', 'parimatch', 'dafabet', 'fairplay', 'mostbet', 'dream11', 'mpl ', 'rummy',
             'bet365', 'draftkings', 'fanduel']
SAFE_EVAL = {'round': round, 'abs': abs, 'min': min, 'max': max, 'int': int, 'float': float, 'sum': sum, 'math': math}


def check_spec(spec, allow_old_sources=False):
    """hard rules of the channel. Fails loudly instead of building or posting something wrong"""
    errs = []
    every = json.dumps(spec, ensure_ascii=False)
    if EM_DASH in every: errs.append('em dash found (channel rule: no em dashes)')
    if EN_DASH in every: errs.append("en dash found (use a comma, colon, 'to' or a hyphen)")
    if spec.get('voice', CHANNEL['voice']) != CHANNEL['voice']: errs.append(f"voice must be {CHANNEL['voice']}")
    post = spec.get('post', {})
    for k in ('post_at', 'slot', 'instagram_caption', 'youtube_title', 'youtube_description'):
        if not post.get(k): errs.append(f'post.{k} is missing')
    if post.get('slot') and post['slot'] not in SLOTS: errs.append(f'post.slot must be one of {list(SLOTS)}')
    try:
        if dt.datetime.fromisoformat(post.get('post_at', '')).tzinfo is None: errs.append('post.post_at needs a timezone, like 2026-11-14T23:30:00+05:30')
    except ValueError:
        errs.append('post.post_at is not an ISO time, like 2026-11-14T23:30:00+05:30')
    # Instagram: disclaimer, a real question just before the hashtags, exactly 5 hashtags with the brand tag, no links
    ig = post.get('instagram_caption', '')
    paras = [x.strip() for x in ig.strip().split('\n\n') if x.strip()]
    tags = re.findall(r'#\w+', ig)
    if len(tags) != 5: errs.append(f'Instagram caption needs exactly 5 hashtags, has {len(tags)}')
    if BRAND_TAG not in [t.lower() for t in tags]: errs.append(f'Instagram caption must include {BRAND_TAG}')
    if paras and not all(w.startswith('#') for w in paras[-1].split()): errs.append('Instagram caption must end with the hashtag line')
    if len(paras) < 2 or not paras[-2].rstrip().endswith('?'): errs.append('Instagram caption: the line just before the hashtags must be a real question')
    if len(ig) > 2200: errs.append('Instagram caption over 2,200 characters')
    if 'http' in ig: errs.append('no links in the Instagram caption')
    # YouTube: title, Sources list, exactly 3 hashtags including #Shorts
    yt = post.get('youtube_description', '')
    if len(post.get('youtube_title', '')) > 70: errs.append('YouTube title over 70 characters')
    if '#' in post.get('youtube_title', ''): errs.append('no hashtags in the YouTube title')
    if 'Sources:' not in yt: errs.append("YouTube description needs a 'Sources:' list")
    if '#Shorts' not in yt: errs.append('YouTube description must include #Shorts')
    if len(re.findall(r'#\w+', yt)) != 3: errs.append('YouTube description needs exactly 3 hashtags')
    for need in ('Education only', '18+'):
        if need not in ig: errs.append(f'Instagram caption must say {need!r}')
        if need not in yt: errs.append(f'YouTube description must say {need!r}')
    # never promotion
    low = every.lower()
    for bad in FORBIDDEN:
        if bad in low: errs.append(f'forbidden (promotion / betting brand): {bad.strip()!r}')
    # sources fetched today; every number backed by a Python-checked calculation
    src = spec.get('sources', [])
    if not src: errs.append('sources is empty: every fact needs a source')
    today = dt.datetime.now(IST).date().isoformat()
    for i, x in enumerate(src):
        if not isinstance(x, dict) or not str(x.get('url', '')).startswith('http'):
            errs.append(f'sources[{i}] needs {{"name", "url", "fetched"}}'); continue
        if not allow_old_sources and x.get('fetched') != today: errs.append(f"sources[{i}] must be fetched today ({today}), has {x.get('fetched')}")
    for i, m in enumerate(spec.get('math', [])):
        try:
            v = eval(m['expr'], {'__builtins__': {}}, SAFE_EVAL)
            if abs(v - float(m['expect'])) > float(m.get('tol', 0.005)) * max(1, abs(float(m['expect']))):
                errs.append(f"math[{i}] {m['expr']} = {v}, but the script says {m['expect']}")
        except Exception as e:
            errs.append(f'math[{i}] could not run: {e}')
    shown = ' '.join(p.get('cap', p.get('say', '')) for p in spec.get('phrases', []))
    if re.search(r'\d', shown) and not spec.get('math'): errs.append('the captions have numbers but math is empty: put every number in math, checked in Python')
    if not any(e.get('at') == -1 for e in spec['scenes'][0]['els']): errs.append('scene 1 needs the hook on frame 0 (build the spec with kit.py)')
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
    check_spec(spec, '--allow-old-sources' in sys.argv)
    if '--check' in sys.argv: print('spec check ok'); return
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
