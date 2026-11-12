"""EP02 caption timing: line times from the generated voiceover, chunk breaks snapped to real pauses."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = [
    "Casinos use five hidden tricks | to keep you playing.",
    "And number one is so sneaky, | most people | never notice it.",
    "Number five.",
    "No clocks, | and almost no windows.",
    "Without a sunset, | you lose track of time.",
    "Number four.",
    "The floor is a maze.",
    "Exits are hard to find.",
    "Machines are impossible to miss.",
    "Number three.",
    "Cash becomes chips.",
    "Plastic doesn't feel like money, | so it's easier to bet more.",
    "Number two.",
    "The free drinks.",
    "They're paid for | by the bets you make | with a slower mind.",
    "But number one | is the craziest.",
    "You bet one dollar.",
    "You win fifty cents.",
    "And the machine celebrates | like you won.",
    "It flashes lights | and plays winning music.",
    "But you just lost | half your money.",
    "Researchers call it | a loss disguised as a win.",
    "The house doesn't need luck.",
    "It just needs time.",
]
EMPHASIS = {"five", "four", "three", "two", "one", "hidden", "sneaky", "never", "clocks", "windows", "sunset",
            "time", "maze", "exits", "machines", "chips", "plastic", "money", "free", "slower", "craziest",
            "dollar", "fifty", "cents", "celebrates", "won", "lights", "music", "lost", "half", "loss", "win", "luck"}
DUR = 51.0

SEGS = json.load(open(os.path.join(HERE, 'vo.segments.json')))
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
            c['end'] = c['words'][-1][2] + 0.4
    return chunks

if __name__ == '__main__':
    for c in caption_chunks():
        print(f"{c['start']:6.2f}-{c['end']:6.2f}  " + ' '.join(w[0] for w in c['words']))
