# King of the Hill — Current Feature Specification

This documents how the "King of the Hill" movie game works today (logic, rules, scoring, and outputs). It is a description of the existing feature, not a proposal to change anything.

---

## 1. What it is
A fast, binary-choice game ("this or that") that learns a player's taste by making them repeatedly pick between two movies, then rewards them with 3 personalized movie discoveries at the end. Internally it's called the "Eliminative Logic Discovery Engine."

- Entry point: a Crown button/menu item that opens a full-screen modal.
- Requires being logged in. If a signed-out user tries to open it, they're prompted to log in first.
- Fixed length: **10 rounds** per game.

---

## 2. The two movie pools
- **Training Pool** — movies the player has already watched (their diary / watch history, up to 200 most recent). These are the movies shown during the 10 rounds.
- **Discovery Pool** — movies the player has **not** watched. These are never shown during play; they are only used at the end to generate recommendations.

**Data requirement:** a player needs at least **6 movies** in their diary for a "full" personalized game. With fewer than 6, the game falls back to showing popular movies spanning different genres (Action, Comedy, Drama, Horror, Documentary) so the game is still playable, but the taste signal is weaker.

---

## 3. How a round works
- Each round shows **two movie posters** side by side with a "vs" in the middle.
- The player picks one of three actions:
  1. **Choose one** (tap it, or swipe it up for a "Super Like").
  2. **Can't Decide** — treats both as equally liked.
  3. **Skip** — discards the matchup, no points.
- The winner becomes the **"King"** and stays on the left (with a crown badge and amber highlight) into the next round. A fresh **challenger** appears on the right.
- Round 1 has no king yet (both cards are fresh). A king appears from round 2 onward.
- A progress bar shows "Round X / 10."

### How the two movies are picked (dissimilarity engine)
The game deliberately pairs **maximally different** movies so each choice reveals a clearer preference. Two movies are scored for "dissimilarity" (0 = identical, 1 = polar opposite) using:
- **Genre difference — 40% weight** (how little their genres overlap).
- **Release-year difference — 30% weight** (50+ years apart = maximum).
- **Director difference — 30% weight** (same director = similar, different = dissimilar).

- Round 1 / fresh pair: it samples up to 20 diary movies, compares all pairs, and shows the single most-dissimilar pair.
- Later rounds: the King stays and the game searches up to 15 remaining diary movies for the one **most unlike the King**.
- If the diary is exhausted or too small, it substitutes popular movies (and, for challengers, uses an "opposite genre" map — e.g. Action ↔ Drama/Romance, Comedy ↔ Horror/Thriller).

---

## 4. Scoring
Every pick earns points that feed the taste profile. The score has three parts multiplied together.

**a) Base points by decision speed (reaction time):**
- Under 2 seconds → **5 points** (strong, instinctive preference)
- 2–5 seconds → **2 points** (standard)
- Over 5 seconds → **1 point** (hesitant)

**b) Super Like (swipe up):** doubles the base points (×2).

**c) Recency weighting** (later rounds count more, since the player has "warmed up"):
- Rounds 1–3 → ×0.8
- Rounds 4–7 → ×1.0
- Rounds 8–10 → ×1.3

**Final points = base × (2 if Super Like) × recency multiplier.**
Example: a Super-Liked fast pick in round 9 = 5 × 2 × 1.3 = 13 points.

**Special actions:**
- **Can't Decide:** both movies get 2 points × recency each; the King is unchanged and only the challenger is swapped.
- **Skip:** 0 points; challenger is discarded, King stays (or a fresh pair appears if there's no King yet).

Points accumulate two ways at once:
- Per **movie** (which champions rose to the top), and
- Per **attribute** — genres, directors, decade/era, and keywords — building an aggregated taste profile.

A small "Current Leaders" strip and a reaction-speed badge ("⚡ Fast!" / "🤔 Hesitant") give live feedback during play.

---

## 5. End of game — the payoff (3 discoveries)
After round 10, the game produces **up to 3 recommendations from the Discovery Pool** (never movies the player has already seen). Candidates are gathered from four strategies, each carrying a starting score and a human-readable reason:

1. **Top genres** (up to 3) → highly-rated films in those genres (rating ≥ 7.0, ≥ 500 votes). Reason: "Your favorite genre: X."
2. **Top directors** (up to 2) → other films by directors the player favored (given a 1.5× boost). Reason: "Directed by X, whom you love."
3. **Similar to the final King** → movies similar to the 10-round champion (high priority). Reason: "Similar to [champion], your 10-round champion."
4. **Fast-choice echoes** → movies similar to titles the player picked quickly. Reason: "Because you quickly chose X over Y."

Candidates are de-duplicated, get a +3 boost if their TMDB rating ≥ 7.5, and are ranked; the top 3 are returned. Each recommendation shows:
- Poster, title, overview, genres, TMDB rating.
- A **Confidence / % Match** (derived from the internal score, capped at 99%).
- A **"Why you'll like this"** one-line reason (from the matching strategy above).

The results screen shows a trophy, medals (🥇🥈🥉), and a "Play Again" button.

---

## 6. Technical behavior worth knowing
- **Endpoints:** `start`, `choose`, `skip`, `cant-decide`. An unknown/expired game returns "session not found" (404).
- **Session storage is in-memory only.** Game progress lives in server memory keyed by a session ID and is deleted when the game ends. Consequences:
  - A backend restart or new deployment **wipes all in-progress games** (players mid-game would get a 404 and have to restart).
  - It assumes a single server process; running multiple replicas would split sessions and break games routed to a different replica.
- **Latency:** each round makes several live TMDB lookups (up to ~15–20 metadata fetches when selecting pairs), so rounds can feel slightly slow on cold data.
- **Movies only** — TV shows are not part of this game.

---

## 7. Known rough edges (current, not yet addressed)
- **"Current Leaders" strip:** the live in-game leaders preview reads a movie title field that the backend doesn't send for these trend items, so it can render as blank/"undefined". The end-game recommendations are unaffected.
- **In-memory sessions vs. deployment:** given the app was just sent to deploy, note that any redeploy or scaling to more than one instance will interrupt active games (see §6).
- **Repeat suggestions possible:** the fallback discovery only filters out already-watched movies, not movies surfaced in a previous game.

---

## Open question for you
This is a read-out of the feature as it exists today. If you want, I can turn any of the rough edges in §7 into fixes (e.g. persist game sessions so deploys/restarts don't kill games, or fix the "Current Leaders" display), or adjust the rules (round count, scoring weights, number of final recommendations). Let me know which, if any.
