# The Rigged Game Studio

Makes and posts Reels / Shorts for The Rigged Game (Instagram and YouTube @the_rigged_game): noir
paper-cutout animation about how casinos really work. For every run, follow `ROUTINE.md` step by step.
Never post directly: queue it, and GitHub Actions posts at `post_at`.

Hard rules:
- Education only: never promote gambling, never name, show or link a betting site or app, no promo codes,
  no "how to win". Every caption says "Education only. Not gambling advice. 18+".
- Write a brief and build the spec with `pipeline/kit.py`; never hand-write scene coordinates or edit specs.
  Check with ONE `make_reel.py --sheet` image, not single stills.
- Voice is Kokoro `am_liam` at speed 1.0, one full line per beat, never spliced. No lone short lines.
- Every fact from a reputable source fetched the same day; every number in `math`, checked in Python.
- No em dashes or en dashes. Instagram caption ends with a real question, then exactly 5 hashtags including
  #theriggedgame. YouTube description has a Sources list and 3 hashtags including #Shorts.
- Instagram AI label and YouTube synthetic-content disclosure stay on.
- Video quality: 1080x1920, 30 fps, H.264 High CRF 14, never lowered or re-compressed.
- Do not change the look (pipeline/noir.py drawing) unless James asks.
- If James replies "skip", create `queue/<id>/SKIP`, commit and push.
- Never put tokens or passwords in files or chat: they live only in GitHub Secrets.
