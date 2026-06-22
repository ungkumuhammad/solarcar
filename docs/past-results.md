# Historical BWSC Challenger-Class Finish Times — last 3 events

**Purpose.** Anchor our simulator's "4-day / ~116 km/h" target against real winning times to
sanity-check feasibility and set a competitive goal. Per CLAUDE.md rule #2 every figure is cited
or marked approximate; per rule #4 confirmed figures are distinguished from derived/approximate ones.

**Events covered.** The genuinely most-recent three World Solar Challenge events: **2025, 2023, 2019**.
(The 2021 event was cancelled for COVID. An earlier project note said "2023/2019/2017"; that predated
the 2025 running — corrected here.) Class = **Challenger** (single-occupant), Darwin→Adelaide ≈ 3,022 km.

**Sourcing note.** Researched 2026-06 via web search. In this environment direct page fetches are
blocked by the network policy (HTTP 403), so figures are taken from search-surfaced reporting
(official BWSC/team pages, university newsrooms, New Atlas, NL Times, Wikipedia). Where only a
finish **time** was reported, the **average speed** is *derived* as 3,022 km ÷ time and labelled
**(derived)**; this matches every independently-cited average to within ~0.1 km/h, so the method
is sound.

---

## 2025 BWSC (held in Aug — first winter running: cooler but less sun)
Closest podium in event history — top three within ~30 minutes.

| Pos | Team | Car | Country | Finish/race time | Avg speed |
|---|---|---|---|---|---|
| 1 | Brunel Solar Team (TU Delft) | Nuna 13 | 🇳🇱 NL | **34 h 54 m 21 s** (confirmed) | **86.6 km/h** (confirmed) |
| 2 | Solar Team Twente | (Twente) | 🇳🇱 NL | **~35 h 09 m** (confirmed, ~15 min back) | ~86.0 km/h (derived) |
| 3 | Innoptus Solar Team (KU Leuven) | — | 🇧🇪 BE | ~35 h 24 m (approx, ~30 min back) | ~85.3 km/h (derived) |

Sources: [NL Times](https://nltimes.nl/2025/08/28/dutch-teams-shine-delft-takes-first-twente-second-world-solar-challenge) ·
[U. Twente newsroom](https://www.utwente.nl/en/news/2025/8/558225/solar-team-twente-finishes-in-second-place-after-an-eventful-final-day) ·
[Innoptus (3rd place)](https://www.innoptus.com/en/blog/innoptus-solar-team-secures-3rd-place-at-the-world-solar-car-championship-after-a-thrilling-race) ·
[BWSC](https://worldsolarchallenge.org/latest-news/brunel-solar-team-charge-into-adelaide)

## 2023 BWSC
| Pos | Team | Car | Country | Finish/race time | Avg speed |
|---|---|---|---|---|---|
| 1 | Innoptus Solar Team (KU Leuven) | Infinite | 🇧🇪 BE | **34 h 04 m 41 s** (confirmed) | ~88.7 km/h (derived) |
| 2 | Solar Team Twente | RED X | 🇳🇱 NL | **~34 h 25 m** (≈16–20 min back*) | ~87.8 km/h (derived) |
| 3 | Brunel Solar Team (TU Delft) | Nuna 12 | 🇳🇱 NL | ~36 h (approx, <2 h after Twente) | ~84 km/h (derived) |

\*The winner's margin over Twente is reported as "sixteen minutes" (Brunel team press) and "~20 min"
(other coverage) — both cited; order Innoptus › Twente › Brunel is consistent across sources.

Sources: [New Atlas](https://newatlas.com/automotive/innoptus-bridgestone-world-solar-challenge-2023-winner/) ·
[Brunel Solar Team (3rd place)](https://brunelsolarteam.com/media/press/brunel-solar-team-secures-third-place-in-world-solar) ·
[U. Twente review](https://www.utwente.nl/en/news/2023/10/1202292/review-solar-team-twente-in-the-world-solar-challenge-2023)

## 2019 BWSC (chaotic year — Vattenfall fire, Twente rollover; neither finished)
| Pos | Team | Car | Country | Finish/race time | Avg speed |
|---|---|---|---|---|---|
| 1 | Agoria Solar Team (KU Leuven) | BluePoint | 🇧🇪 BE | ~34 h 52 m (12 min ahead of Tokai) | **86.6 km/h** (confirmed) |
| 2 | Tokai University | Tokai Challenger | 🇯🇵 JP | **~35 h 04 m** (confirmed) | **86.1 km/h** (confirmed) |
| 3 | University of Michigan | Electrum | 🇺🇸 USA | **~37 h 56 m** (confirmed) | **79.6 km/h** (confirmed) |

Sources: [New Atlas](https://newatlas.com/automotive/world-solar-challenge-winner-2019-agoria/) ·
[Axalta / Agoria win](https://www.axalta.com/gb/en_GB/news-releases/agoria-solar-team-becomes-world-champion-at-the-2019-bridgestone.html) ·
[Agoria](https://www.agoria.be/en/themes/about-us/agoria-solar-team/world-solar-challenge-2019-dreams-do-come-true-for-the-belgian-solar-team-world-champions) ·
[Wikipedia: World Solar Challenge](https://en.wikipedia.org/wiki/World_Solar_Challenge)

---

## Comparison vs our simulator

| Metric | Real winners (2019–2025) | Our `optimized_regulation` sim |
|---|---|---|
| Winning race time | **~34–35 h** (3rd places ~36–38 h) | finishes in **4 days** |
| Official average speed | **~80–88 km/h** (winners ~86–88) | **~95.9 km/h** distance ÷ effective-drive (31.5 h) |
| Moving average (within drive window) | not published | **116.2 km/h** |

**Reading the numbers.** The WSC "average speed" is distance ÷ total **official driving time**
(the 08:00–17:00 windows summed across the ~4 race days, ≈ 34–35 h for a winner). Our simulator's
**95.9 km/h** is the like-for-like figure (3,022 km ÷ 31.5 h effective drive); the **116.2 km/h**
headline is the *moving* average that excludes control stops, so it is not directly comparable to the
published number.

**Takeaways.**
- **The 4-day finish target is realistic** — every event's top three finished inside ~4 days, and
  even 2017 (slower cars, 81 km/h winner) finished. ✅
- **Our pace sits at the optimistic edge.** On the comparable basis our sim covers the route ~10%
  faster than the *fastest-ever* winners (96 vs ~86–88 km/h). That is consistent with the documented
  **solar-saturation / over-powered finding** (the optimized car has surplus it can't legally spend
  at NT 130 / SA 110), but it also flags the model as **optimistic**: real cars lose time to weather,
  cloud, wind, traffic, strategy and tyre/driver changes that the deterministic sim omits.
- **Competitive goal.** To beat the field, target a *race time* near **34 h** (≈ 88–90 km/h on the
  official basis). Our model already implies this is achievable on paper — the open question is
  whether real-world losses (next on the build list: wind, cloud/weather, location-based irradiance)
  erode the margin. These historical times are the yardstick to test future model refinements against.
