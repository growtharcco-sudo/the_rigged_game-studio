"""Caption timing: 21 spoken segments (from silence detection) mapped to the 21 script phrases."""

SEGMENTS = [
    (0.00, 1.35, "In the 1800s,"),
    (1.53, 4.80, "a Yorkshire mill engineer | walked into | the Monte Carlo casino."),
    (5.45, 6.40, "He didn't place a bet."),
    (6.96, 7.73, "He just watched."),
    (8.43, 9.05, "For a month,"),
    (9.40, 11.44, "he wrote down | every number that landed."),
    (12.18, 13.27, "He knew machines."),
    (13.73, 16.44, "And he knew | no spinning wheel | is perfectly balanced."),
    (16.98, 18.27, "One wheel had a flaw."),
    (18.83, 20.99, "Some numbers came up | more often than they should."),
    (21.61, 22.44, "So he bet on them."),
    (22.99, 24.12, "And he kept winning."),
    (24.74, 25.66, "Over a few days,"),
    (25.93, 28.10, "he took more than | 2 million francs."),
    (28.50, 30.03, "That's millions | in today's money."),
    (30.76, 32.04, "The casino fought back."),
    (32.56, 35.34, "Wheels were redesigned | so the trick | could never work again."),
    (36.07, 37.80, "He went home | and bought houses."),
    (38.36, 40.93, "He beat the casino | the only way | it can be beaten."),
    (41.42, 42.10, "Not with luck."),
    (42.60, 43.35, "With maths."),
]

# Words that get gold emphasis in captions
EMPHASIS = {"1800s", "monte", "carlo", "watched", "month", "machines", "balanced", "flaw",
            "winning", "2", "million", "francs", "millions", "fought", "never", "houses",
            "luck", "maths"}


def words_with_times():
    out = []  # (word, start, end, segment_index)
    for si, (s, e, text) in enumerate(SEGMENTS):
        words = [w for w in text.split() if w != "|"]
        weights = [len(w.strip(",.'")) + 2 for w in words]
        total = sum(weights)
        t = s
        for w, wt in zip(words, weights):
            d = (e - s) * wt / total
            out.append((w, t, t + d, si))
            t += d
    return out


def caption_chunks(max_words=4):
    """Split each segment into chunks of <= max_words, balanced. Returns list of
    dicts with words (list of (word,start,end)), show_start, show_end."""
    words = words_with_times()
    chunks = []
    for si, (s, e, text) in enumerate(SEGMENTS):
        ws = [w for w in words if w[3] == si]
        i = 0
        for part in text.split("|"):
            n = len(part.split())
            chunks.append({"words": ws[i:i + n], "seg": si})
            i += n
    for i, c in enumerate(chunks):
        c["start"] = c["words"][0][1] - 0.05
        if i + 1 < len(chunks):
            nxt = chunks[i + 1]["words"][0][1] - 0.05
            end_spoken = c["words"][-1][2]
            # hold through short pauses, clear on long ones
            c["end"] = nxt if nxt - end_spoken < 0.9 else end_spoken + 0.35
        else:
            c["end"] = 43.55
    return chunks


if __name__ == "__main__":
    for c in caption_chunks():
        print(f'{c["start"]:6.2f}-{c["end"]:6.2f}  ' + " ".join(w[0] for w in c["words"]))
