"""Reel kit: turn a short brief into a full noir spec using ready-made, tested scene blocks.

Why: hand-writing every scene (coordinates, timings) and checking 15 to 20 stills per Reel is what costs
Claude usage. With the kit, a Reel is a short brief; layouts are fixed and already checked, and one
contact sheet (make_reel.py --sheet) replaces the stills.

Brief (briefs/<id>.json):
{
  "id": "003_roulette", "episode": "03", "series": "Casino Secrets",
  "keywords": ["house", "edge"],                       # words that light up gold in captions (numbers are automatic)
  "beats": [                                           # one beat = one full spoken line (never a lone 2-word line)
    {"say": "...", "cap": "...|...", "pause": 0.45,    # cap optional ('|' = caption break), pause = silence before
     "show": {"kind": "fan", ...}},                    # optional: starts a new scene at this beat
    {"say": "...", "show": [{"kind": "countdown", ...}, {"kind": "cards", "from_word": 2, ...}]},
    ...                                                # a list = several scenes in one line; later ones need
  ],                                                   #   "from_word" (scene starts when that word is spoken)
  "cover": {"kicker": "...", "big": "...", "sub": "..."}, "sources": [...], "post": {...}
}

Time fields inside a show ("..._at", item "beat"): a beat number counted from the scene's first beat
(0 = the scene's own beat), or {"beat": n, "delay": sec} or {"beat": n, "word": w}.

Scene kinds (all in the noir paper-cutout style; legacy/ has the episodes they come from):
  HOOKS
  title      big (year or word, cut-out card), tag (small red label)       EP01 night casino + walking gambler
  fan        title, secret ("TOP SECRET"), secret_at                       countdown hook: numbered cards + red "?"
  clock_hunt stamp ("NOT FOUND"), stamp_at                                 wall with a missing clock, magnifier
  STORY
  watch      eye_at                                                        felt table, wheel, gambler, no-bet chip -> eye
  notebook   days, unit ("DAY"), dur                                       candlelit notebook, numbers being written
  balance    wheel_at, fig1, fig2, callout                                 blueprint gears -> wobbling wheel
  odds       hot=[numbers], bars_at, label, line                           lucky pockets glow + frequency chart
  streak     streak_at, wins                                               chips on lucky pockets + W tags
  counter    value, prefix, suffix, decimals, unit, count_at, dur, after, after_at   chips + number counting up
  patched    header, stamp ("PATCHED"), fix_at, stamp_at                   guards, wrench sweeps the wheel
  town       place                                                         sunset, houses rising
  book       year, boss, title=[2 lines], boss_at, open_at                 book opens, former boss behind it
  EXPLAINERS
  countdown  n, sub                                                        big flipping number card (#5 ... #1)
  cards      items=[{text, icon, beat, word, delay}] (max 3), stamp, stamp_at   paper cards slide in. icons: clock,
                                                                           window, sunset, chip, cash, wheel, drink, dice
  maze       headers=[3], exit_at, machines_at                             blueprint maze, lost visitor, EXIT, machines
  chips      before, after, note, flip_at, note_at                         cash bills flip into chips
  drinks     front, back=[2 lines], strike_at, flip_at, woozy, woozy_at    free drink with a price tag that flips
  puppet     label                                                         a giant hand works the gambler on strings
  chart      title, x_label, y_label, house                                blueprint chart: your money down, house up
  slot       bet, won, banner, loss, mask_label, spin_at, party_at, lost_at, mask_at   loss disguised as a win
  ENDING
  ending     wrong ("LUCK"), right (hero word), strike_at, right_at, visual ("hourglass"|"none"),
             eq (small top label), outro (default true: end card held after the last line)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
W = 1080
CAPTION_TOP = 1290   # captions sit around y 1440; nothing may be drawn below this line except ground/footer
MIN_BEAT_WORDS = 5   # Kokoro drags very short lines


def kinds_doc():
    return __doc__


def block(kind, s, b, nb):
    """elements for one scene. b = global index of the scene's first beat, nb = beats in the scene"""
    def at(v=0, default_delay=0.0):
        if isinstance(v, dict):
            out = {'b': b + min(int(v.get('beat', 0)), nb - 1)}
            if 'word' in v: out['w'] = int(v['word'])
            if 'delay' in v or default_delay: out['d'] = v.get('delay', default_delay)
            return out
        n = b + min(int(v), nb - 1)
        return [n, default_delay] if default_delay else n
    A = at(0)
    def L(text, y, at_, size=44, bg='rust', fg='paper', rot=-3, font='Mono-Bold', **k):
        return dict(type='label', text=text, y=y, at=at_, size=size, bg=bg, fg=fg, rot=rot, font=font, **k)
    G = lambda y=1255, c=None: dict(type='ground', y=y, **({'color': c} if c else {}))

    if kind == 'title':
        return [{'type': 'bg', 'look': 'night'},
                {'type': 'mascot', 'at': A, 'x': 300, 'y': 830, 's': 0.82, 'drift': -60, 'walk': 90, 'walk_dur': 2.5},
                {'type': 'word', 'at': A, 'text': s['big'], 'y': 400, 'size': 190, 'rot': -3, 'pop': 'back'},
                L(s.get('tag', ''), 520, A, size=40, rot=-3)] if s.get('tag') else \
               [{'type': 'bg', 'look': 'night'},
                {'type': 'mascot', 'at': A, 'x': 300, 'y': 830, 's': 0.82, 'drift': -60, 'walk': 90, 'walk_dur': 2.5},
                {'type': 'word', 'at': A, 'text': s['big'], 'y': 400, 'size': 190, 'rot': -3, 'pop': 'back'}]
    if kind == 'fan':
        els = [{'type': 'bg', 'look': 'hall'}, G(1250), {'type': 'mascot', 'at': A, 'x': 190, 'y': 830, 's': 0.78},
               {'type': 'fan', 'at': A, 'n': s.get('n', 5)},
               L(s['title'], 300, A, size=66, bg='ink', fg='gold', font='Inter-Black')]
        if s.get('secret'):
            els.append({'type': 'stamp', 'text': s['secret'], 'x': W / 2 + 150, 'y': 520, 'size': 84, 'rot': -12,
                        'at': at(s.get('secret_at', {'beat': 1, 'delay': 1.0}))})
        return els
    if kind == 'clock_hunt':
        st = at(s.get('stamp_at', {'beat': 1, 'delay': 0.0}))
        return [{'type': 'bg', 'look': 'hall'}, {'type': 'wallclock', 'at': A, 'stop_at': st}, G(1250),
                {'type': 'mascot', 'at': A, 'x': -60, 'y': 820, 's': 0.78, 'walk': 260, 'walk_dur': 1.4},
                {'type': 'stamp', 'text': s.get('stamp', 'NOT FOUND'), 'y': 660, 'size': 120, 'rot': -8, 'at': st}]
    if kind == 'watch':
        return [{'type': 'bg', 'look': 'hall'}, {'type': 'table_wheel', 'at': A}, G(1250),
                {'type': 'mascot', 'at': A, 'x': 205, 'y': 780, 's': 0.8, 'rise': 160},
                {'type': 'nobet_eye', 'at': A, 'eye_at': at(s.get('eye_at', 1))}]
    if kind == 'notebook':
        return [{'type': 'bg', 'look': 'candle'},
                {'type': 'tally', 'at': A, 'days': s.get('days', 30), 'unit': s.get('unit', 'DAY'), 'dur': s.get('dur', 3.3)}, G(1255)]
    if kind == 'balance':
        e = {'type': 'balance', 'at': A, 'wheel_at': at(s.get('wheel_at', 1))}
        for k in ('fig1', 'fig2', 'callout'):
            if s.get(k): e[k] = s[k]
        return [{'type': 'bg', 'look': 'blueprint', 'rot': 1.5}, e, G(1260)]
    if kind == 'odds':
        e = {'type': 'wheel_odds', 'at': A, 'bars_at': at(s.get('bars_at', 1)),
             'label': s.get('label', 'HOW OFTEN EACH NUMBER LANDED'), 'line': s.get('line', 'EXPECTED')}
        if s.get('hot'): e['hot'] = s['hot']
        return [{'type': 'bg', 'look': 'paper'}, e, G(1262)]
    if kind == 'streak':
        return [{'type': 'bg', 'look': 'paper', 'glow': 0.25}, {'type': 'streak', 'at': A, 'streak_at': at(s.get('streak_at', 1)),
                'wins': s.get('wins', 9)}, G(1255)]
    if kind == 'counter':
        e = {'type': 'counter', 'at': A, 'value': s['value'], 'prefix': s.get('prefix', ''), 'suffix': s.get('suffix', ''),
             'decimals': s.get('decimals', 0), 'count_at': at(s.get('count_at', 0)), 'dur': s.get('dur', 3.0),
             'chips': s.get('chips', True)}
        if s.get('unit'): e['unit'] = s['unit']
        if s.get('after'): e['after'] = s['after']; e['after_at'] = at(s.get('after_at', nb - 1))
        return [{'type': 'bg', 'look': 'paper'}, e, G(1255)]
    if kind == 'patched':
        fx = at(s.get('fix_at', {'beat': 0, 'delay': 1.4})); st = at(s.get('stamp_at', {'beat': 1, 'delay': 0.0}))
        return [{'type': 'bg', 'look': 'red'},
                {'type': 'mascot', 'at': A, 'x': 130, 'y': 820, 's': 0.75, 'rise': 200},
                {'type': 'mascot', 'at': A, 'x': W - 130, 'y': 820, 's': 0.75, 'rise': 200},
                {'type': 'patch', 'at': A, 'fix_at': fx},
                {'type': 'stamp', 'text': s.get('stamp', 'PATCHED'), 'y': 730, 'size': 150, 'rot': -10, 'at': st},
                L(s.get('header', 'THE CASINO FIGHTS BACK'), 250, A, bg='ink', rot=-2), G(1255)]
    if kind == 'town':
        return [{'type': 'bg', 'look': 'sunset'}, {'type': 'town', 'at': A}, G(1255), L(s['place'], 300, A, rot=-2)]
    if kind == 'book':
        els = [{'type': 'bg', 'look': 'paper', 'glow': 0.3}]
        bt = at(s.get('boss_at', {'beat': 0, 'delay': 1.2}))
        if s.get('boss'):
            els.append({'type': 'mascot', 'at': bt, 'x': W / 2 + 260, 'y': 560, 's': 0.72, 'rise': 180, 'fade': 0.7, 'color': '#2a1a12'})
        els.append({'type': 'book', 'at': A, 'open_at': at(s.get('open_at', {'beat': 0, 'delay': 2.6})),
                    'title': s.get('title', ['DESIGNING', 'CASINOS'])})
        if s.get('year'): els.append(L(s['year'], 330, A, size=64, font='Inter-Black', pop='big'))
        if s.get('boss'): els.append(dict(L(s['boss'], 470, bt, size=34, bg='ink', rot=3), x=W / 2 + 230, delay=0.2))
        els.append(G(1255))
        return els
    if kind == 'countdown':
        n = s['n']
        return [{'type': 'bg', 'look': 'dark', 'rays': True}, {'type': 'numcard', 'at': A, 'n': n},
                L(s.get('sub', ''), 1240, A, size=54, bg='paper' if n == 1 else 'ink', fg='rust' if n == 1 else 'gold',
                  rot=2, font='Inter-Black', delay=0.2),
                L(f'TRICK #{n}' if not s.get('label') else s['label'], 300, A, size=46, delay=0.2)]
    if kind == 'cards':
        items = []
        for i, it in enumerate(s['items'][:3]):
            ref = {'beat': it.get('beat', 0), 'delay': it.get('delay', 0.0), **({'word': it['word']} if 'word' in it else {})}
            items.append({'text': it['text'], 'icon': it.get('icon', 'chip'), 'at': at(ref)})
        els = [{'type': 'bg', 'look': 'study'}, {'type': 'cards', 'at': A, 'items': items}]
        if s.get('stamp'):
            st = at(s.get('stamp_at', nb - 1))
            els += [{'type': 'dim', 'at': st}, {'type': 'stamp', 'text': s['stamp'], 'y': 720, 'size': 150, 'rot': -9, 'at': st, 'delay': 0.25}]
        return els
    if kind == 'maze':
        return [{'type': 'bg', 'look': 'blueprint', 'rot': 1.2},
                {'type': 'maze', 'at': A, 'exit_at': at(s.get('exit_at', 1)), 'machines_at': at(s.get('machines_at', 2)),
                 'headers': s.get('headers', ['THE MAZE', 'WHERE IS THE EXIT?', 'MACHINES EVERYWHERE'])}, G(1262)]
    if kind == 'chips':
        fl = at(s.get('flip_at', {'beat': 0, 'delay': 0.7}))
        els = [{'type': 'bg', 'look': 'paper', 'glow': 0.25, 'glow_y': 780}, {'type': 'cash_chips', 'at': A, 'flip_at': fl}]
        if s.get('before'): els.append(L(s['before'], 330, A, size=56, bg='ink', font='Inter-Black', until=fl, delay=0.2))
        if s.get('after'): els.append(L(s['after'], 330, fl, size=64, font='Inter-Black', pop=True, delay=0.1))
        if s.get('note'): els.append(L(s['note'], 1200, at(s.get('note_at', min(1, nb - 1))), size=40, bg='ink', fg='gold', rot=2))
        els.append(G(1262))
        return els
    if kind == 'drinks':
        e = {'type': 'drink', 'at': A, 'front': s.get('front', 'FREE'), 'back': s.get('back', ['PAID BY', 'YOUR BETS']),
             'flip_at': at(s.get('flip_at', 1))}
        if 'strike_at' in s: e['strike_at'] = at(s['strike_at'])
        els = [{'type': 'bg', 'look': 'hall'}, e]
        if s.get('woozy'):
            e['woozy_at'] = at(s.get('woozy_at', {'beat': nb - 1, 'delay': 1.5}))
            els.append(L(s['woozy'], 330, e['woozy_at'], size=48, bg='ink', fg='gold'))
        els.append(G(1255))
        return els
    if kind == 'puppet':
        return [{'type': 'bg', 'look': 'red'}, {'type': 'puppet', 'at': A},
                L(s.get('label', 'ONE JOB'), 1180, A, size=60, bg='paper', fg='rust', font='Inter-Black', pop='big', delay=0.1),
                G(1262, '#2a0b08')]
    if kind == 'chart':
        e = {'type': 'chart', 'at': A}
        for k in ('title', 'x_label', 'y_label', 'house'):
            if s.get(k): e[k] = s[k]
        return [{'type': 'bg', 'look': 'blueprint', 'rot': -1.2}, e, G(1262)]
    if kind == 'slot':
        e = {'type': 'slot', 'at': A, 'spin_at': at(s.get('spin_at', 1)), 'party_at': at(s.get('party_at', 2)),
             'lost_at': at(s.get('lost_at', 4)), 'mask_at': at(s.get('mask_at', 5))}
        for k in ('bet', 'won', 'banner', 'loss', 'mask_label', 'reels'):
            if s.get(k): e[k] = s[k]
        return [e, G(1262, '#120707')]
    if kind == 'ending':
        st = at(s.get('strike_at', {'beat': 0, 'delay': 1.1})); rt = at(s.get('right_at', {'beat': nb - 1, 'delay': 1.0}))
        els = [{'type': 'bg', 'look': 'paper', 'glow': 0.3, 'glow_y': 760}]
        if s.get('visual', 'none') == 'hourglass':
            els += [{'type': 'hourglass', 'at': A, 'dur': s.get('dur', 3.3)},
                    {'type': 'word', 'at': A, 'text': s.get('wrong', 'LUCK'), 'font': 'Inter-Black', 'size': 110, 'x': W / 2 - 200, 'y': 300,
                     'rot': -6, 'strike_at': st, 'tear_rot': 10, 'tear_drop': 50, 'tear_fade': 0.5},
                    {'type': 'word', 'at': rt, 'text': s['right'], 'size': 170, 'x': W / 2 + 110, 'y': 500, 'rot': 4,
                     'card': 'ink', 'ink': 'gold', 'pop': 'slam'}]
        else:
            if s.get('eq'): els.append(L(s['eq'], 300, at({'beat': 0, 'delay': 0.6}), size=40, rot=2))
            els += [{'type': 'word', 'at': A, 'text': s.get('wrong', 'LUCK'), 'font': 'Inter-Black', 'size': 190, 'y': 560,
                     'rot': -3, 'strike_at': st},
                    {'type': 'word', 'at': rt, 'text': s['right'], 'size': 210, 'y': 900, 'rot': 2, 'card': 'ink', 'ink': 'gold',
                     'pop': 'slam', 'glow': True}]
        els.append(G(1255))
        els.append({'type': 'text', 'at': at({'beat': 0, 'delay': 1.0}), 'text': 'THE RIGGED GAME', 'y': 1720, 'size': 34,
                    'alpha': 0.8, 'footer': True})
        if s.get('outro', True):
            els.append({'type': 'outro', 'at': ['end', 0.35]})
        return els
    raise ValueError('unknown scene kind: ' + kind)


def build_spec(brief):
    beats = brief['beats']; phrases = []; starts = []   # starts: (beat, show, from_word)
    for i, bt in enumerate(beats):
        ph = {'say': bt['say']}
        if bt.get('cap'): ph['cap'] = bt['cap']
        ph['pause'] = bt.get('pause', 0.45); phrases.append(ph)
        sh = bt.get('show')
        for j, one in enumerate(sh if isinstance(sh, list) else ([sh] if sh else [])):
            if j and 'from_word' not in one: raise ValueError(f'beat {i}: extra shows need "from_word"')
            starts.append((i, one, one.get('from_word')))
    if not starts or starts[0][0] != 0 or starts[0][2]: raise ValueError("beat 0 must have a 'show' (the hook frame)")
    scenes, progress, progress_end = [], [], None
    for k, (b, sh, fw) in enumerate(starts):
        nxt = starts[k + 1][0] if k + 1 < len(starts) else len(beats)
        nb = max(1, nxt - b + (1 if k + 1 < len(starts) and starts[k + 1][2] else 0))
        start = b if fw is None else {'b': b, 'w': fw}
        scenes.append({'start': start, 'kind': sh['kind'], 'els': block(sh['kind'], sh, b, nb)})
        if sh['kind'] == 'countdown': progress.append(b)
        if sh['kind'] == 'ending' and progress and progress_end is None: progress_end = b
    for e in scenes[0]['els']:            # the hook frame is fully visible at frame 0 (thumbnail + first look)
        a = e.get('at', -1)
        if a == 0 or (isinstance(a, list) and a[0] == 0) or (isinstance(a, dict) and a.get('b') == 0 and 'w' not in a):
            e['at'] = -1; e.pop('delay', None)
    spec = {'id': brief['id'], 'episode': brief.get('episode', '00'), 'series': brief.get('series', ''),
            'voice': brief.get('voice', 'am_liam'), 'speed': brief.get('speed', 1.0), 'hold': brief.get('hold', 2.6),
            'caption_keywords': brief.get('keywords', []), 'phrases': phrases, 'scenes': scenes}
    if len(progress) >= 3:
        spec['progress'] = progress
        spec['progress_end'] = progress_end if progress_end is not None else 'end'
    for k in ('cover', 'sources', 'post'): spec[k] = brief[k]
    return spec


def layout_check(spec):
    """cheap automatic check so the sheet only needs one look: text inside the frame, nothing too wide,
    nothing in the caption zone, captions at most 2 lines, no line too short for the voice, no em dashes"""
    import noir
    problems = []
    if '—' in json.dumps(spec, ensure_ascii=False): problems.append('em dash found (channel rule: no em dashes)')
    for si, sc in enumerate(spec['scenes']):
        for e in sc['els']:
            for (text, fn, size, cx, y, pad, maxw) in noir.texts(e):
                if not text: continue
                w = noir.text_w(text, fn, size) + pad
                if w > maxw: problems.append(f'scene {si} ({sc["kind"]}): too wide ({int(w)}px > {maxw}): "{text}"')
                elif maxw >= 980 and (cx - w / 2 < 20 or cx + w / 2 > W - 20):
                    problems.append(f'scene {si} ({sc["kind"]}): off the frame edge: "{text}"')
                if y > CAPTION_TOP and not e.get('footer'):
                    problems.append(f'scene {si} ({sc["kind"]}): in the caption zone (y {y}): "{text}"')
    for bi, ph in enumerate(spec['phrases']):
        if len(ph['say'].split()) < MIN_BEAT_WORDS:
            problems.append(f'beat {bi}: only {len(ph["say"].split())} words ("{ph["say"]}"). Short lines make the voice drag; merge it with the next line')
        cap = ph.get('cap', ph['say'])
        parts = [p.split() for p in cap.split('|')] if '|' in cap else noir.auto_chunks(cap.split())
        for p in parts:
            f = noir.font('Inter-Black', 84); sp = f.measureText(' ')
            lines, cw = 1, 0
            for w in p:
                wd = f.measureText(w.upper())
                if cw and cw + sp + wd > 900: lines += 1; cw = 0
                cw += (sp if cw else 0) + wd
            if lines > 2: problems.append(f'beat {bi}: caption chunk wraps to {lines} lines: "{" ".join(p)}". Add a | break')
    return problems


if __name__ == '__main__':
    brief = json.load(open(sys.argv[1])); spec = build_spec(brief)
    probs = layout_check(spec)
    root = os.path.dirname(HERE)
    out = os.path.join(root, 'specs', f'{spec["id"]}.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(spec, open(out, 'w'), indent=1, ensure_ascii=False)
    print('wrote', os.path.relpath(out, root), f'({len(spec["scenes"])} scenes, {len(spec["phrases"])} beats)')
    if probs: print('LAYOUT PROBLEMS:\n  ' + '\n  '.join(probs)); sys.exit(1)
    print('layout ok')
