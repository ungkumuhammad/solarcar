# MEMORY.md — Solar Car BWSC 2027 (canonical project memory)

> **This is the project's living memory. Read it at the start of every session before any work.**
> Update it **only when the user says "update memory" (or "compress")** — prepend a new dated
> entry under "Session Log" (newest first) and refresh "Current Project State".
> Older detailed entries are archived in `docs/session-memory.md`.

---

## Current Project State (carry-forward — keep this current)

**Deployment / repo**
- Repo `ungkumuhammad/solarcar` is **public**; **`main` contains everything** (all feature work merged).
- Interactive dashboard is **LIVE**: **https://ungkumuhammad.github.io/solarcar/**
- Auto-deploys via `.github/workflows/pages.yml` on any push that touches `index.html` (or the workflow). Pages source = GitHub Actions (already enabled).
- Housekeeping: 7 merged `claude/*` branches still exist on the remote (all verified ancestors of `main`, safe to delete): `dashboard-authentication-e035ph`, `continuation-wcnnku`, `dynamic-speed-profile-viz-27tnlj`, `goal-speed-limit-filter-n3pfiz`, `solar-car-losses-tivgr7`, `solar-challenge-2027-plan-nsj4yl`, `youthful-dirac-fmkyjn`. **Neither the managed git proxy (`git push --delete` blocked) nor the GitHub MCP tools can delete remote branches/refs here** — remove them from the GitHub Branches UI (purely cosmetic).

**The dashboard (`index.html`) — current focus for refinement**
- **Gated behind Supabase Auth login.** Username: `ungkumzulhilmi` (maps to `ungkumzulhilmi@solarcar.local`). Supabase project `npgioimtpwyeiwtwjfdu.supabase.co`; anon key embedded in `index.html` (safe to expose). Credentials/password managed via Supabase dashboard. To add/revoke members: Authentication → Users — no code change needed.
- Single self-contained file: inline CSS + JS, **Chart.js + Supabase JS via CDN**. No build step.
- It is a **faithful JS port of the Python model** — losses, solar/atmosphere, speed strategy (bisection), whole-race battery budget + client-side calibration, location-based control stops, per-territory speed limits, regen-to-battery, and the time-step loop.
- **Timestep is 10 min** (dashboard `RACE.dt=10`, Python `race.time_step_min=10`, since 2026-06-24) — the speed profile is on a 10-minute basis. (Superseded the earlier 30-min default; all figures below are dt=10.)
- **INVARIANT: the JS must stay in sync with the Python model.** Re-verified at dt=10: optimized legal **3022 km / 117.0 km/h / 96.7% SoC**; challenger **2984.1 km / 92.8 km/h / 13.0% SoC**; target-20% (limit left open) → **20.7% / 127.7 km/h**.
- **Goal-seek now leaves the posted speed limit open** (200 km/h analysis ceiling) so it always returns a result; any driving above NT130/SA110 is **remarked** (distance over, peak, amount over) and flagged analysis-only (§3.31.6). Applies to both the target-SoC plan and the finish-time Goal-Seek, in CLI + dashboard. **Non-goal-seek runs are unchanged and stay race-legal** (report zero exceedance).
- **Goal-Seek has TWO modes (dashboard, `gsMode` selector):**
  - **Finish by day & time** — bidirectional: if the spec already finishes **at/before** the target → **PACE DOWN** to a single constant cruise (slowest legal speed still meeting the target, `ceil` to 0.1 km/h) → lower avg speed + energy surplus; if it finishes **after** → existing param speed-up (open-limit + exceedance remark). **Day 5 selectable** (`GS_DAY_MAX=5`); picking a day > `PARAMS.days` bumps `PARAMS.days` so it runs as a longer race. Cruise lock clears on preset/slider/ref-team change.
  - **Average speed** (`goalSeekAvg()`, dynamic since 2026-06-24) — keeps the **DYNAMIC** speed strategy (speed varies with solar, SoC, grade, air density) and bisection-calibrates a new **`speedScale`** lever in `simulate()` (multiplies the dynamic speed, re-clipped to `[vmin, posted cap]`) so the resulting race **average equals the requested value**. Runs a 7-day calibration then trims `PARAMS.days` to the actual finish day. Reports energy demand (avg/peak W, kWh harvested), finish, SoC. Flags the **posted-cap ceiling** if the target avg is unreachable legally (e.g. optimized max ≈ 120 km/h); if the battery can't carry the route at that pace it **advises checked-param changes**. Verified: target 100 → speed 85.2–110.5 averaging 100.2; 86.6 → 68.5–96.4 averaging 86.8; 140 rejected (cap-bound). **NOT a flat line.**
  - The day+time mode reuses `p.fixedSpeed` (constant cruise, mirrors Python `--speed`); avg mode uses `p.speedScale` (dynamic). Both clear on preset/slider/ref/target change; physics in `simulate()` untouched.
- **Winning-team dropdown now DRIVES the sim (dashboard, 2026-06-23):** selecting a team runs OUR configured car at that team's avg pace (`fixedSpeed=ref.avg`), auto-extending race days via `daysToFinishAtFixed()` (cap 7; ~80–88 km/h → 5 days) so it finishes. Speed/SoC/solar/elevation/power/finish all reflect it; cards show team pace, ref race time, our finish, SoC at finish; `#note` shows the scenario + day auto-extend. Deselect → reverts to dynamic. (Replaces the old overlay-only behavior.)
- Controls: preset (Challenger / Optimized / **Custom** — auto-set when sliders are hand-tuned) + sliders for all car/race params, target-SoC and v-max-override toggles, a **Display→speed-table threshold** slider, and a **Goal-Seek** panel (target finish day+time → tick which non-regulation params it may tune → bisects an improvement factor and writes the found spec onto the sliders; solar 6 m² & battery 3.056 kWh are hard-excluded; reports already-met / infeasible-earliest). Outputs: summary cards, 5 charts (speed w/ substantial-change markers, SoC, power-stack, elevation, irradiance), a **per-day summary table** (SoC start/end, dist, avg speed), and the speed-profile table (units in headers; Solar-in = irr×area and Solar-act = harvested-after-efficiency columns). **Speed-profile table (2026-06-24): shows EVERY 10-min step by default (toggle `tableEvery` / "Speed table: every 10-min step" in Preset & strategy; off → substantial-change filter via `tableThr`), labels every control stop by location (Katherine, Daly Waters, … Port Augusta — name recorded in the JS trace `T.stopName`; Python via `control_stop_name_at()` in `environment/route.py`), and includes parked-but-charging rows (speed 0, irradiance > 0 at dawn 6:30–8:00 / dusk 17:00–18:30).**
- **Sidebar and main panel scroll independently** (Preset & strategy / Goal-Seek stay visible while the main panel scrolls).

**Model facts (BWSC 2027, simulator)**
- 4-day race, Darwin→Adelaide 3022 km; regulation window 08:00–17:00; **9 location-based control stops** (30 min each, charge from solar during halt).
- **Posted speed limits NT 130 / SA 110 km/h** (§3.31.6 — no derestricted section). `--v-max` override is analysis-only (not race-legal).
- Whole-race battery strategy via `--target-soc` (calibrated by bisection in `RaceSimulator.run_to_target_soc`).
- Regen-to-battery implemented (`gravity_power` + surplus recovery); **≈0 Wh on the gentle wsc route** (verified ~62 kWh on a forced −8% slope — only matters with steeper elevation).
- Official specs: solar **6.0 m²** (§2.4.2), battery **3.056 kWh / 11 MJ** (§2.5.2). Presets: `challenger_class()` (baseline), `optimized_regulation()` (target).

**Headline engineering finding**
- At legal speed caps the `optimized_regulation` car is **near solar-saturated** — at 110 km/h midday solar output exceeds demand, so the battery stays high (finishes ~96.7% SoC at dt=10) and the surplus is **unspendable legally**. Spending it down to a low target SoC requires exceeding posted limits. Goal-seek does this automatically (leaves the limit open → target 20% reaches **20.7% at avg 127.7 km/h**, dt=10) and **remarks** that the plan is analysis-only, not race-legal. Design implication: the car is over-powered for legal speeds.

**File map**
- `main.py` (CLI) · `models/` (car, race) · `losses/` (10 loss models, incl. `gradient.py` `gravity_power`) · `environment/` (solar_model, atmosphere, route + `load_control_stops_km`/`load_speed_limits_km`) · `simulation/` (simulator, speed_strategy, energy_budget, plots, tables) · `index.html` (dashboard) · `data/` (route.csv, irradiance/, elevation/) · `regulations/` · `CLAUDE.md` (project instructions) · `docs/session-memory.md` (archive).
- Run examples: `python main.py --preset optimized_regulation --route wsc [--plot --table --csv] [--target-soc 0.20] [--v-max 150]`.

**Historical benchmark** — `docs/past-results.md` records the Challenger-class podium for the last 3 events (2025/2023/2019): winners finish in **~34–35 h at ~86–88 km/h**. Surfaced in the dashboard via the **"Winning-team reference"** dropdown (avg-pace line + sim-vs-ref cards). Use these as the yardstick for future model refinements.

**Suggested next work** (from CLAUDE.md "What to Build Next"): location-based irradiance (wire `data/irradiance/`), sensitivity analysis, wind model, cloud/weather model, race strategy optimizer. (Dashboard refinement round — Goal-Seek, table/solar columns, per-day SoC, scroll & preset fixes, **Winning-team reference** — is **done**.)

---

## Session Log (newest first)

### 2026-06-24 — Dynamic average-speed Goal-Seek + every-10-min speed table  ✅ MERGED TO MAIN (PR #10, 3cc5db0)
#### Accomplished (branch `claude/dashboard-authentication-e035ph` → **merged to `main`**)
- **Average-speed Goal-Seek made DYNAMIC** (was a flat constant line). New **`speedScale`** lever in
  `simulate()` scales the dynamic-strategy speed (still shaped by solar/SoC/grade/air-density),
  bisection-calibrated so the race **average = the requested value**. 7-day calibration, then trims
  `PARAMS.days` to the finish day. Reports demand/finish/SoC; flags the posted-cap ceiling; advises
  params if the battery can't carry the route. Verified: 100→85.2–110.5 avg 100.2; 86.6→68.5–96.4 avg
  86.8; 140 rejected (max ≈120).
- **Speed-profile table shows every 10-min step** by default (toggle `tableEvery`); stops named,
  parked-charging rows shown. (User reported the table wasn't showing 10-min detail.)
#### Key Decisions / Findings
- `speedScale` and `fixedSpeed` are mutually exclusive levers (day+time pace-down = constant cruise;
  avg mode = dynamic scale); both clear on preset/slider/ref/target change. `simulate()` physics
  unchanged → JS↔Python parity holds (Python avg mode is the `--speed` constant, dashboard-only dynamic).
#### Next steps
- Location-based irradiance (wire `data/irradiance/`), then wind / cloud / sensitivity / optimizer.

---

### 2026-06-24 — 10-min profile, avg-speed Goal-Seek, Day 5, control-stop names  ✅ MERGED TO MAIN (PR #9)
#### Accomplished (branch `claude/dashboard-authentication-e035ph` → **merged to `main`**, 044d44d)
- **10-min timestep** everywhere: dashboard `RACE.dt=10`, Python `race.time_step_min=10`. Speed
  profile is now on a 10-minute basis. Re-verified JS == Python: optimized **3022/117.0/96.7%**,
  challenger **2984.1/92.8/13.0%** (supersedes the 30-min figures of 116.2/100% and 2931.7/93.1/16.4%).
- **Speed-profile table**: every control stop labelled by location (Katherine … Port Augusta) — name
  recorded in the trace (`T.stopName` in JS; `control_stop_name_at()` in `environment/route.py` for the
  Python CLI table). Also shows **parked-but-charging rows** (speed 0, irradiance > 0 at dawn/dusk).
- **Goal-Seek average-speed mode** (`goalSeekAvg()`): drive a constant requested pace, report energy
  demand + finish + SoC, and advise the car-parameter changes needed to sustain it. Mode selector
  (`gsMode`) toggles between this and the day+time mode.
- **Day 5 selectable** in Goal-Seek (`GS_DAY_MAX=5`); a day > `PARAMS.days` extends the race.
- Updated verified figures + dashboard notes in `CLAUDE.md`.
#### Key Decisions / Findings
- Answered the user's D5 question first: at Brunel's 86.6 km/h the sim **drives ~34.9 h** (= their race
  time) but, rationed to the 9 h/day window minus 4.5 h of control stops (31.5 h over 4 days → 2728 km
  by D4 17:00), the last 294 km spill into **D5 ~11:30**. Not a bug — calendar finish ≠ continuous
  drive-time; realistic for BWSC.
- dt=10 shifted headline numbers; **changed Python default too** to preserve the JS↔Python invariant
  (both re-verified identical).
- Branch cleanup: all 7 merged `claude/*` branches confirmed ancestors of `main` but **cannot be deleted
  from this environment** (git proxy + GitHub MCP both lack ref deletion) — must use the Branches UI.
#### Next steps
- Location-based irradiance (wire `data/irradiance/`), then wind / cloud / sensitivity / optimizer.
- Optional: sweep remaining secondary numbers in `CLAUDE.md`/`docs` to dt=10 (headline blocks done).

---

### 2026-06-23 — Goal-Seek pace-down + winning-team scenario  ✅ MERGED TO MAIN (PR #7)
#### Accomplished (branch `claude/dashboard-authentication-e035ph` → **merged to `main`**, e31b2ae)
- **Goal-Seek bidirectional** (`goalSeek()`): later-than-achievable target now **paces the car
  DOWN** to a constant cruise that lands exactly on the target (lower avg speed, energy surplus)
  instead of "already finishes — no change". Earlier targets still use the param speed-up path.
  Cruise lock (`PARAMS.fixedSpeed`) clears on preset/slider/ref-team change.
- **Winning-team dropdown drives the sim** (`run()` + new `daysToFinishAtFixed()`): selecting a
  team runs our car at their avg pace, auto-extending race days to finish; all charts/cards/finish
  reflect the scenario. Replaces the old overlay-only behavior.
- Both reuse the existing `p.fixedSpeed` lever — **`simulate()` physics unchanged** (mirrors Python
  `--speed`). Posted-limit clipping + exceedance logic preserved.
#### Key Decisions / Findings
- Verified (DOM-stubbed node): baselines unchanged (optimized 3022/116.2/100%, challenger
  2931.7/93.1/16.4%); pace-down to D4 14:00 → **106.1 km/h cruise, exact finish**; Brunel 86.6 →
  **5 days**, finishes 3022 km (driving-time ≈ their 34.9 h).
- Pace-down speed rounds **UP** (ceil 0.1 km/h) so finish stays ≤ target (rounding down overshot by
  one 30-min timestep).
- For the **optimized** car SoC surplus reads ~0 (already solar-saturated at 100%); the visible
  benefit is the lower avg speed. Cars finishing <100% show the surplus directly.
- **New standing workflow rule** (recorded in `CLAUDE.md` Principle #0): **merge to `main` after the
  user approves a session** — no need to ask each time (still never merge without approval).
#### Next steps
- Location-based irradiance (wire `data/irradiance/`), then wind / cloud / sensitivity / optimizer.

---

### 2026-06-23 — Supabase Auth login gate on the dashboard  ✅ MERGED TO MAIN
#### Accomplished (branch `claude/dashboard-authentication-e035ph` → **merged to `main`**)
- Dashboard (`index.html`) is now **gated behind a Supabase Auth login**. The full simulator/charts
  stay hidden until a valid session is established — no more public access.
- **Login overlay** — full-screen card (dark-theme matched), Username + Password fields, error message
  on bad credentials, **Sign out** button in the header (hidden until logged in).
- **Session persists** across reloads via Supabase `localStorage`; Sign out clears it.
- Username `ungkumzulhilmi` maps internally to `ungkumzulhilmi@solarcar.local`; password verified
  server-side by Supabase (never stored in the page).
- Supabase project `npgioimtpwyeiwtwjfdu.supabase.co`; anon public key embedded (safe to expose —
  access enforced server-side by Supabase Auth).
- Dashboard bootstrap (`buildControls(); run();`) now runs only inside `startApp()`, called after
  a confirmed session (fixes Chart.js canvas-sizing inside hidden containers).

#### Key Decisions / Findings
- **Supabase Auth** chosen over a client-side hash gate — password never appears in source.
- **Username login UX preserved** via `<username>@solarcar.local` email mapping convention.
- To add more team members: create `<username>@solarcar.local` users in the Supabase dashboard
  (Authentication → Users) — **no code change needed**.
- Manage access (revoke, reset passwords) entirely from the Supabase dashboard.

#### Next steps
- Remaining simulator work: location-based irradiance, wind model, cloud/weather, sensitivity
  analysis, race strategy optimizer (unchanged from previous sessions).

---

### 2026-06-22 — Goal-seek leaves speed limit open + remarks on exceedance  ✅ MERGED TO MAIN + LIVE
#### Accomplished (branch `claude/goal-speed-limit-filter-n3pfiz` → **merged to `main`** via `--no-ff`; Pages redeployed, change is **live** at the dashboard URL)
- Goal-seek was returning **no usable result**: the posted caps (NT 130 / SA 110, §3.31.6) leave
  the optimized car solar-saturated, so target-SoC floored at ~95.7% and the finish-time Goal-Seek
  reported "not reachable". Fixed by **leaving the limit open during a goal-seek** (replaced by a
  `200 km/h` analysis ceiling, `OPEN_LIMIT_CEILING_KMH` / `OPEN_CEILING`) so it always finds a result,
  with a **non-blocking ⚠ remark** when the solution drives above the posted limit.
- New `speed_limit_exceedance()` (`environment/route.py`) + JS mirror `speedExceedance()` — scans the
  driven trace, evaluates the limit at each step's **start** position (mirrors how the sim clips), 0.5
  km/h tolerance ⇒ **legal runs report zero**. Reports distance-over / peak / max-over.
- Wired through: `simulator.py` (`open_limits` flag, `_v_max_at`, `run()` populates budget fields,
  `run_to_target_soc` opens the limit during calibration); `energy_budget.py` (4 `over_limit_*` fields
  + `print_summary` remark); `main.py` (target-soc messaging + header). Dashboard: `simulate`
  (`p.openLimits`), `calibrate`, `run` (note remark), finish-time `goalSeek` (remark).
- Scope (confirmed with user): **both** goal-seek features, **dashboard + CLI**, **automatic** (no toggle).

#### Key Decisions / Findings
- **JS↔Python parity re-verified** (node, DOM-stubbed): target-20% → scale 15.0, **20.2% SoC, 128.6 km/h**,
  exceedance ~2248 km / peak 157.4 / +47.4 — identical both sides. Legal run unchanged (116.2 / 100% / 0
  exceedance). `--v-max` path still works and now also shows the remark.
- Boundary fix: evaluating the posted limit at step **end** falsely flagged the 65 km step crossing the
  NT→SA border at 130; using the **start** position removed the false positive.

#### Next steps
- Done: merged to `main`, dashboard redeployed (Pages run #7). Branch left on remote (cosmetic).

---

### 2026-06-22 — Historical BWSC finish times + dashboard "Winning-team reference"  ✅ (branch `claude/continuation-wcnnku`)
#### Accomplished
- **`docs/past-results.md`** — Challenger-class podium (1st/2nd/3rd) for the **last 3 events: 2025,
  2023, 2019**, with team/car/country, official race time, avg speed, and citations. Winners finish
  in **~34–35 h at ~86–88 km/h** (3rd places ~36–38 h / ~80–84 km/h).
- **Discrepancy flagged & resolved (rule #3):** the queued task said "2023/2019/2017", but a **2025
  BWSC happened** (most recent) — user chose the genuinely-last-3 (2025/2023/2019). 2021 = COVID.
- **Dashboard (`index.html`):** new **"Winning-team reference"** dropdown (9 historical podium
  entries) — selecting one adds a dashed **avg-pace line** on the speed chart + 4 cards (ref avg
  speed, ref race time, sim-vs-ref speed Δ, sim-vs-ref time Δ). Purely a reference overlay; **does
  not touch the model.** Verified additive (node DOM-stub: optimized 3022/116.2/100%, challenger
  2931.7/93.1/16.4%, target-20 → 20.2% all unchanged).
#### Key Decisions / Findings
- **4-day finish is realistic** (every event's top-3 finished inside ~4 days). Our sim's like-for-like
  pace (96 km/h, dist÷effective-drive) is ~10% **faster than the fastest-ever winners (~86–88)** —
  consistent with the solar-saturation finding, but flags the model as **optimistic** (omits
  weather/wind/cloud/traffic). Competitive race-time goal ≈ **34 h**.
- **Env note:** WebFetch is blocked here (HTTP 403 on all domains); only WebSearch works — citations
  are to search-surfaced pages.
#### Next steps
- Location-based irradiance (wire `data/irradiance/`), then wind / cloud / sensitivity / optimizer —
  test each refinement against the historical times in `docs/past-results.md`.

---

### 2026-06-22 — Dashboard refinements: Goal-Seek, table/solar columns, per-day SoC, scroll & preset fixes
#### Accomplished (all in `index.html`; merged to `main` via PR #4)
1. **Goal-Seek** (new) — pick a target finish day+time and tick which non-regulation params it may
   tune; it bisects an improvement factor (lerp current→best slider bound), snaps to slider steps,
   and applies the found spec to the sliders. **Solar area (6 m²) and battery (3.056 kWh) are
   hard-excluded.** Branches: "already met", "infeasible — earliest is …", and success (lists each
   before→after change). Added `finishT` to the JS `simulate()` return to measure finish clock time.
2. **Speed-profile table** — units in headers (`Dist, km`, `Speed, km/h`, …); dropped the Δ column;
   added **Solar-in** (irr × panel area) and **Solar-act** (harvested after the efficiency selection).
3. **Control-stop rows named** from `data/route.csv` (`CONTROL STOP — Alice Springs`, …).
4. **Per-day summary table** — SoC start/end, distance covered, avg speed per day.
5. **Granularity** — speed-table change threshold is now an adjustable slider (Display group); the
   speed chart marks the substantial-change points.
6. **Independent scroll** for sidebar vs main; **preset dropdown fixed** (persists selection + Custom
   state on hand-tuning, so Challenger ⇄ Optimized works).

#### Key Decisions / Findings
- Goal-Seek param choice = **user picks** (checklist), not a fixed dial.
- Verified (node, DOM-stubbed) that core physics is unchanged: optimized 3022/116.2/100%, challenger
  2931.7/93.1/16.4%, target-20% floor 95.7%. Optimized car naturally finishes **~Day 4 11:30**; even
  maxing every loss param it can't finish before **~Day 4 11:00** — it is speed-limited (NT 130/SA 110),
  consistent with the solar-saturation finding. Goal-Seek's useful range is widest from the Challenger spec.

#### Next steps
- Location-based irradiance (wire `data/irradiance/`), then sensitivity analysis / wind / cloud / optimizer.

### 2026-06-22 — Visualization, whole-race strategy, regen, live dashboard
**Accomplished (three work bodies, all merged to `main` and pushed):**
1. **Speed-profile visualization + location-based control stops** — matplotlib dashboard
   (`simulation/plots.py`, `--plot` → `output/dashboard.png` + `power_by_day.png`),
   substantial-speed-change table + CSV export (`simulation/tables.py`, `--table/--csv`),
   extended `EnergyBudget` per-timestep traces (driving **and** parked/charging steps so
   cross-day SoC carryover and evening/morning charging are visible). Control stops moved
   from a "2 stops/day, end day early" abstraction to **9 real checkpoint km** with a hard
   17:00 stop (`models/race.py`, `simulator.py`).
2. **Whole-race battery strategy + posted speed limits + regen** — `--target-soc` with
   bisection calibration (`run_to_target_soc`); per-territory caps NT 130 / SA 110 via
   `route.py` `load_speed_limits_km` + `speed_limit_at_distance` (+ `--v-max` override);
   regen-to-battery via `gravity_power` and descent-surplus recovery into the pack.
3. **Interactive dashboard + deploy** — built `index.html` (in-browser JS port, Chart.js),
   `.github/workflows/pages.yml`; merged PR #3 to `main`; made the repo **public**; enabled
   Pages (Source = GitHub Actions); **dashboard is live** at the URL above.

**Key decisions / findings:**
- Solar-saturation finding (see Current State) — surplus unspendable at legal speeds.
- JS dashboard verified to match the Python model exactly.
- Memory system: established this `MEMORY.md` as the **canonical** memory; `CLAUDE.md`
  rewired to read/update it; `docs/session-memory.md` archived.

**Next steps (user starting a new session):** continue **refining the dashboard**; keep the
JS port in sync with any Python model change.

---

*Older detailed entries: see `docs/session-memory.md` (archive).*
