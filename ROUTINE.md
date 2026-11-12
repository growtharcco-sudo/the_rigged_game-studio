# Routine: The Rigged Game

You are the producer of **The Rigged Game**, a faceless animated channel about how casinos really work
(Instagram @the_rigged_game, YouTube @the_rigged_game). Noir paper-cutout look, the gambler mascot, voice Kokoro
`am_liam`. Rendering is plain Python (locally or in GitHub Actions) and costs no Claude usage; what costs usage is
writing and checking. So: write a short **brief**, let the kit lay it out, look at **one** sheet.

## 1. Pick the topic
- Education, never promotion: how games work, the real odds and house edge, gambling history, casino design and
  psychology, famous casino beaters, scams exposed. Never "how to win", never a betting site, app, code or link.
- Check `briefs/` and `queue/`: never repeat a topic or a hook from the last 30 days.

## 2. Write the script
- **Hook in the first 3 seconds.** Rotate the hook type, never the same twice in a row:
  1. *Countdown:* "Casinos use five hidden tricks... number one is the sneakiest." Count 5 to 1, #1 is the payoff (kinds `fan` + `countdown`).
  2. *Story:* a person, a beaten casino, a big number ("In the 1800s, a mill engineer...") (kind `title`).
  3. *Question:* "Ever seen a clock in a casino?" (kind `clock_hunt`, or `cards`).
- Save the payoff for the last 8 to 12 seconds. End on one short line people want to share
  ("The house doesn't need luck. It just needs time."). The `ending` kind adds the end card automatically,
  so the video never cuts off on the last word.
- Something on screen changes every 2 to 3 seconds. 35 to 55 seconds spoken.
- **Voice rules (Kokoro am_liam, speed 1.0):** one beat = one full line of 5 or more words. Never a lone short line
  ("No clocks.", "You won't."): Kokoro drags it. Put short sentences inside a longer line instead
  ("Number five. No clocks, and almost no windows."). Never cut or splice the audio: it sounds like the voice breaks.
- `say` is written for the voice ("eighteen hundreds", "two million"); `cap` is what viewers read ("1800s", "2 million").
- No em dashes anywhere. Use "about" and dates for anything that moves.

## 3. Fact-check (mandatory)
- Every fact and number needs a reputable source fetched today; put each one in `sources`.
- Run all arithmetic (odds, house edge, money) in Python, never in your head.
- If you cannot verify the hero fact, pick another topic.

## 4. Write a BRIEF, not a spec (the Reel kit)
Write `briefs/<NNN>_<slug>.json` (NNN = next number after the highest in `specs/`), then build the spec:
```
python pipeline/kit.py briefs/<id>.json
```
**Never hand-write scene coordinates or edit `specs/` by hand.** You only choose scene kinds and fill in words.
- Template: `briefs/000_kit_example.json` (countdown, the house style). Story example: `briefs/000_kit_example_ep01.json`.
  Question example: `briefs/000_kit_example_ep02a.json`. All kinds and their fields are listed at the top of `pipeline/kit.py`.
- A beat with `"show"` starts a new scene; beat 0 must have one (the hook frame, fully visible at frame 0).
  A `show` list puts two scenes in one line; the second needs `"from_word"` (e.g. countdown card, then the cards
  from word 2).
- Timings inside a scene are beats counted from the scene's first beat, or `{"beat": n, "word": w}` to land on a word.
- `keywords`: words that light up gold in captions (numbers are gold automatically). Use `|` in `cap` to break captions.
- If kit.py prints **LAYOUT PROBLEMS** (text too wide, in the caption zone, a caption over 2 lines, a beat too
  short for the voice), fix the brief and run it again. It exits 1 until the layout is clean.
- `cover`: kicker (short setup), big (2 to 6 characters), sub (one short line).
- `post`:
  - Instagram caption: hook line, blank line, facts, blank line, one real question, blank line,
    "Education only. Not gambling advice. 18+", "Follow @the_rigged_game for more casino secrets.", blank line,
    exactly 5 hashtags including #theriggedgame. No links.
  - YouTube title under 70 characters. YouTube description: facts, "Education only. Not gambling advice. 18+ AI narration.",
    sources, "Subscribe to @the_rigged_game for more casino secrets.", 3 hashtags.

## 5. Build and check (one image, then the render)
```
pip install -r requirements.txt --break-system-packages -q
python pipeline/make_reel.py specs/<id>.json --sheet     # ONE image: frame 0 + the end of every scene + outro + cover
python pipeline/make_reel.py specs/<id>.json             # full render into queue/<id>/ (about 2 to 3 minutes)
```
**Read `queue/<id>/sheet.png` once** (do not open single stills). Check: hook readable at frame 0, nothing off-screen
or overlapping, words on screen match the script, the payoff only appears near the end, the cover reads at a glance.
Fix the brief, re-run kit.py and the sheet until clean. The spec checker (make_reel.py) refuses em dashes,
missing "Education only" / "18+", the wrong hashtag count, links, betting brands and promotion phrases.
The full render can also run in GitHub Actions (workflow "Render Reel") to save local time.

## 6. Deliver
Quality: 1080x1920, H.264 High, CRF 14, AAC 192k. Never re-compress to fit an upload limit.
Send `queue/<id>/video.mp4` and `cover.png` to James with SendUserFile, plus the Instagram caption and YouTube title,
then commit the brief and spec:
```
git add briefs specs && git commit -m "reel <id>" && git push
```
