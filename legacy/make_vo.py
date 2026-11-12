"""Generate a voiceover with Kokoro. Each script line is spoken in one go (natural flow),
then sentence start/end times inside the line are found from its real pauses.
Usage: python3 make_vo.py script.txt out.wav [voice] [speed]
Writes out.wav plus out.segments.json: [start, end, sentence, line_index] per sentence."""
import sys, json, re
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

src, out = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else 'am_liam'
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
SR = 24000
LINE_GAP, LEAD, TAIL = 0.45, 0.15, 0.6

k = Kokoro('/home/claude/tts/kokoro-v1.0.onnx', '/home/claude/tts/voices-v1.0.bin')
lines = [l.strip() for l in open(src) if l.strip()]

def trim(a):
    thr = 0.01 * np.max(np.abs(a))
    nz = np.where(np.abs(a) > thr)[0]
    return a[max(0, nz[0] - 600): nz[-1] + 1200]

def quiet_runs(a, thr=0.06, min_len=0.03):
    """quiet stretches (start, end, depth) in seconds; depth = mean level, lower is quieter"""
    hop = int(0.01 * SR)
    rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    lv = rms / rms.max()
    out, i = [], 0
    while i < len(lv):
        if lv[i] < thr:
            j = i
            while j < len(lv) and lv[j] < thr: j += 1
            if (j - i) * 0.01 >= min_len: out.append((i * 0.01, j * 0.01, float(lv[i:j].mean())))
            i = j
        else:
            i += 1
    return out

BREATH = 0.2  # extra pause added at each sentence break inside a line

parts, segs, t = [np.zeros(int(LEAD * SR), np.float32)], [], LEAD
for li, line in enumerate(lines):
    audio, sr = k.create(line, voice=voice, speed=speed, lang='en-us')
    audio = trim(audio).astype(np.float32)
    dur = len(audio) / SR
    sents = [x.strip() for x in re.split(r'(?<=[.?!])\s+', line) if x.strip()]
    cuts = []
    if len(sents) > 1:
        runs = [r for r in quiet_runs(audio) if 0.2 < r[0] < dur - 0.2]
        def plen(x):
            ph = k.tokenizer.phonemize(x, 'en-us')
            return sum(1 for c in ph if c.isalpha() or c in 'ɚɪʊəɑɔæʌɛŋθðʃʒɹɾʔː') + 3 * sum(c in '.?!' for c in ph) + 1.5 * ph.count(',')
        lens = [plen(x) for x in sents]
        total = sum(lens)
        acc = 0
        for x, lx in zip(sents[:-1], lens[:-1]):
            acc += lx
            est = dur * acc / total
            near = [r for r in runs if abs((r[0] + r[1]) / 2 - est) < 0.35]
            if not near and x.lower().startswith('number'):
                # countdown numbers: accept the softest dip before the next word (often a stop like the k in cash)
                near = [r for r in quiet_runs(audio, thr=0.2, min_len=0.02) if abs((r[0] + r[1]) / 2 - est) < 0.2]
            if near:
                r = max(near, key=lambda r: (r[1] - r[0]) - 2 * r[2] - 0.3 * abs((r[0] + r[1]) / 2 - est))
                if r in runs: runs.remove(r)
                real = ((r[1] - r[0]) >= 0.08 and r[2] < 0.025) or r[2] < 0.016
                if x.lower().startswith('number') and abs((r[0] + r[1]) / 2 - est) < 0.2:
                    real = True  # always give the countdown number a beat
                print(f'  line {li} break {len(cuts)}: est {est:.2f} run {r[0]:.2f}-{r[1]:.2f} depth {r[2]:.3f} -> {"pause" if real else "too weak, no breath"}')
                if not real and abs((r[0] + r[1]) / 2 - est) > 0.2:
                    cuts.append((est, est, False))  # weak dip far from the estimate is likely inside a word
                else:
                    cuts.append((r[0], r[1], real))
            else:
                print(f'  line {li} break {len(cuts)}: est {est:.2f} no quiet spot -> no breath')
                cuts.append((est, est, False))
    # rebuild the line with a short breath at each sentence break
    pieces, times, pos, local = [], [], 0.0, 0.0
    for c0, c1, real in cuts:
        mid = (c0 + c1) / 2
        seg = audio[int(pos * SR):int(mid * SR)]
        times.append((local, local + (c0 - pos)))
        br = 0.0  # never cut silence into a line: it sounds like the voice is breaking
        pieces += [seg, np.zeros(int(br * SR), np.float32)]
        local += len(seg) / SR + br
        pos = mid
        times[-1] = (times[-1][0], times[-1][1])
        local_start_next = local + (c1 - mid)
        times.append(('start', local_start_next))
    seg = audio[int(pos * SR):]
    pieces.append(seg)
    end_last = local + len(seg) / SR
    starts = [0.0] + [x[1] for x in times if x[0] == 'start']
    ends = [x[1] for x in times if x[0] != 'start'] + [end_last]
    audio = np.concatenate(pieces); dur = len(audio) / SR
    for si, x in enumerate(sents):
        segs.append([round(t + starts[si], 2), round(t + ends[si], 2), x, li])
    parts.append(audio); t += dur
    gap = TAIL if li == len(lines) - 1 else LINE_GAP
    parts.append(np.zeros(int(gap * SR), np.float32)); t += gap
wav = np.concatenate(parts)
wav = wav / np.max(np.abs(wav)) * 0.89
sf.write(out, wav, SR, subtype='PCM_16')
json.dump(segs, open(out.rsplit('.', 1)[0] + '.segments.json', 'w'), indent=1)
print(f'{len(wav) / SR:.2f}s, {len(lines)} lines, {len(segs)} sentences')
