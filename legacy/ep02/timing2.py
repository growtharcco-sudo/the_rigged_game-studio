"""EP02 caption timing: line times from the generated voiceover, chunk breaks snapped to real pauses."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = [
    "Walk into most casinos, | and try to find a clock.",
    "You won't.",
    "No clocks.",
    "Few windows.",
    "No sunset | to remind you it's late.",
    "That's not an accident.",
    "In the year 2000, | a former casino boss | wrote a whole book | on designing casinos.",
    "His rules?",
    "Low ceilings.",
    "Maze-like paths.",
    "Machines everywhere you turn.",
    "Real cash disappears too.",
    "You hold chips, | so it doesn't feel like money.",
    "And the free drinks?",
    "They're not free.",
    "They're paid for | by the bets you make | with a slower mind.",
    "Every detail has one job.",
    "Keep you playing.",
    "Because the longer you stay, | the more the maths wins.",
    "The house doesn't need luck.",
    "It just needs time.",
]
EMPHASIS = {"clock", "won't", "clocks", "windows", "sunset", "accident", "2000", "book", "ceilings",
            "maze-like", "machines", "chips", "money", "free", "slower", "one", "playing", "maths",
            "luck", "time"}
DUR = 40.33

SEGS = json.load(open(os.path.join(HERE, 'vo_liam.segments.json')))
SIL = [tuple(map(float, l.split())) for l in open(os.path.join(HERE, 'silences.txt'))]

def wlen(w):
    return len(w.strip(",.'?")) + 2

def caption_chunks():
    chunks = []
    for (s, e, *_), text in zip(SEGS, TEXT):
        parts = [p.split() for p in text.split('|')]
        total = sum(wlen(w) for p in parts for w in p)
        inner = [(a, b) for a, b in SIL if s + 0.1 < a and b < e - 0.05]
        bounds = [s]
        acc = 0
        for p in parts[:-1]:
            acc += sum(wlen(w) for w in p)
            est = s + (e - s) * acc / total
            near = [x for x in inner if abs((x[0] + x[1]) / 2 - est) < 0.6]
            if near:
                a, b = min(near, key=lambda x: abs((x[0] + x[1]) / 2 - est))
                inner.remove((a, b))
                bounds.append((a, b))
            else:
                bounds.append((est, est))
        bounds.append(e)
        # chunk i spans [end of previous pause, start of next pause]
        for i, p in enumerate(parts):
            cs = bounds[i] if i == 0 else bounds[i][1]
            ce = bounds[i + 1] if i == len(parts) - 1 else bounds[i + 1][0]
            tot = sum(wlen(w) for w in p)
            t, words = cs, []
            for w in p:
                d = (ce - cs) * wlen(w) / tot
                words.append((w, t, t + d))
                t += d
            chunks.append({'words': words})
    for i, c in enumerate(chunks):
        c['start'] = c['words'][0][1] - 0.05
        end_spoken = c['words'][-1][2]
        if i + 1 < len(chunks):
            nxt = chunks[i + 1]['words'][0][1] - 0.05
            c['end'] = nxt if nxt - end_spoken < 0.9 else end_spoken + 0.35
        else:
            c['end'] = DUR - 0.1
    return chunks

if __name__ == '__main__':
    for c in caption_chunks():
        print(f"{c['start']:6.2f}-{c['end']:6.2f}  " + ' '.join(w[0] for w in c['words']))
