# The Rigged Game Studio

Noir paper-cutout Reels for **The Rigged Game** (@the_rigged_game): how casinos really work.

```
briefs/<id>.json  --pipeline/kit.py-->  specs/<id>.json  --pipeline/make_reel.py-->  queue/<id>/video.mp4 + cover.png
```

- `pipeline/kit.py`: brief -> spec. 21 tested scene kinds with fixed coordinates, plus a layout check.
- `pipeline/noir.py`: the renderer (skia). Every drawing is ported unchanged from the hand-made episodes in `legacy/`.
- `pipeline/voice.py`: Kokoro `am_liam`, one call per full line, never spliced.
- `pipeline/make_reel.py`: channel rule check, `--sheet` (one check image), full render.
- `legacy/`: the original hand-coded episodes (EP01 Monte Carlo, EP02 No clocks, EP02 countdown) for reference.
- `brand/`: profile picture and YouTube banner.

Posting (free: public repo + GitHub Actions + GitHub Pages):
- Claude renders, puts the video and cover on the `media` branch (served by Pages), commits `queue/<id>/post.json`
  with `post_at` and pushes. `post.yml` waits for the exact time (checks every 2 minutes; cron is only a backup)
  and posts to Instagram (Graph API, system user token, AI label on, direct-upload fallback) and YouTube
  (Data API v3, public, synthetic-content disclosure on, cover as thumbnail). `post-now.yml` posts instantly.
- `queue/<id>/SKIP` cancels a post. Results land in `posted/<id>/result.json`.
- `tools/check_keys.py` and `tools/deep_check.py` test the keys without posting anything publicly.

See `SETUP.md` for the one-time setup and `ROUTINE.md` for the daily routine.

Scene layouts that repeated across EP01, EP02 and the EP02 countdown, and became kinds:
hooks (`title`, `fan`, `clock_hunt`), the casino hall with the gambler (`watch`, `drinks`, `fan`), blueprint
explainers (`balance`, `maze`, `chart`), wheel scenes (`odds`, `streak`, `patched`), paper cards and labels
(`cards`, `countdown`), money moments (`counter`, `chips`, `slot`), story beats (`notebook`, `book`, `town`,
`puppet`) and the luck-vs-X `ending` with the held end card.

Fonts: Inter, Playfair Display, JetBrains Mono (SIL Open Font License).
