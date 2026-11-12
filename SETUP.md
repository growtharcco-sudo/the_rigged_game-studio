# One-time setup

Everything is free: public repo + GitHub Actions + GitHub Pages. Keys go only into GitHub's encrypted Secrets,
never into a file or a chat. Claude guides each step one screen at a time.

## A. GitHub
1. Repo `growtharcco-sudo/the_rigged_game-studio`, Public, Claude GitHub app has access (done).
2. Claude pushes the `media` branch (it holds the site pages and the deep-check test video).
3. Repo -> Settings -> Pages -> Source *Deploy from a branch* -> `media` / `(root)` -> Save.
   Check: https://growtharcco-sudo.github.io/the_rigged_game-studio/ shows the channel page.

## B. Instagram key (never expires): reuse the system user "unhyped-poster" and the app "Real Number Studio"
1. @the_rigged_game must be a Professional (Business) account linked to a NEW Facebook Page "The Rigged Game".
   **Trap:** switching Instagram to Business can silently create a NEW business portfolio. The Page and the
   Instagram account must end up in the business portfolio **"The Real Number"**. If a new portfolio appears,
   move the assets into "The Real Number".
2. business.facebook.com -> portfolio "The Real Number" -> Accounts -> add the Page "The Rigged Game" and the
   Instagram account @the_rigged_game.
3. Settings -> Users -> System users -> **unhyped-poster** -> Assign assets: the Page and the Instagram account,
   Full control. **Trap:** reopen the system user afterwards and check both show **Full access**
   (it can say "Nothing assigned yet").
4. Generate new token -> app **Real Number Studio** -> expiration **Never** -> permissions `instagram_basic`,
   `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management` -> that is
   `IG_TOKEN` (starts with EAA). Copy it straight into GitHub Secrets (step D), not into the chat.
5. `IG_USER_ID`: leave it out at first. The "Check keys" run prints it.

## C. YouTube key: a NEW Google Cloud project for this channel (its own daily upload quota)
1. console.cloud.google.com -> New project "Rigged Game Studio" -> APIs & Services -> enable **YouTube Data API v3**.
2. Google Auth Platform (OAuth consent screen): External. **Branding**: app name "The Rigged Game Studio",
   home page https://growtharcco-sudo.github.io/the_rigged_game-studio/, privacy
   https://growtharcco-sudo.github.io/the_rigged_game-studio/privacy.html, terms
   https://growtharcco-sudo.github.io/the_rigged_game-studio/terms.html, authorized domain
   `growtharcco-sudo.github.io`. **Trap:** "Publish app" stays greyed out until these Branding links and the
   domain are saved.
3. Data access: add scopes `.../auth/youtube.upload` and `.../auth/youtube`.
4. Audience: **Publish app** -> "In production".
5. Clients -> Create client -> type **Desktop app** -> Download JSON.
6. On the laptop: `pip3 install google-auth-oauthlib`, then
   `python3 tools/get_youtube_token.py ~/Downloads/client_secret_XXXX.json` and sign in with the
   **The Rigged Game** channel (@the_rigged_game). It prints `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
   **Trap:** `redirect_uri_mismatch` = wrong client type (must be Desktop) or an older client_secret file in
   Downloads. Run the script on the newest file.
   Uploads go PUBLIC directly, with the "altered or synthetic content" disclosure on.

## D. Secrets
Repo -> Settings -> Secrets and variables -> Actions -> New repository secret, one each:
`IG_TOKEN`, `IG_USER_ID`, `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
Paste only the value (if a label or spaces slip in, the code cleans them).

## E. Test (posts nothing publicly). Claude runs these by pushing to `checks/` and reads the run notices.
1. **Check keys**: prints the Instagram username, quota and the YouTube channel name and IDs (never key values).
2. **Deep check**: Instagram processes a test Reel without publishing it; YouTube gets an UNLISTED test upload
   that is checked (stays unlisted = public uploads work), given the thumbnail, then deleted.
3. One real end-to-end post (slot `test`), then the daily task is switched on.

## F. Scheduled task (Claude)
ONE cloud task, "The Rigged Game daily", runs `ROUTINE.md` section A once a day.
It needs "Skip all approvals" (Automatically approve) on and no connectors it doesn't use.
The whole account has at most 5 scheduled runs a day.
