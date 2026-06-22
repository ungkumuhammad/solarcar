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
- Housekeeping: 3 old merged branches still exist on the remote (`claude/solar-car-losses-tivgr7`, `claude/solar-challenge-2027-plan-nsj4yl`, `claude/dynamic-speed-profile-viz-27tnlj`). The managed git proxy here **cannot delete remote branches**; remove them from the GitHub Branches UI if desired (purely cosmetic — all fully merged).

**The dashboard (`index.html`) — current focus for refinement**
- Single self-contained file: inline CSS + JS, **Chart.js via CDN**. No build step.
- It is a **faithful JS port of the Python model** — losses, solar/atmosphere, speed strategy (bisection), whole-race battery budget + client-side calibration, location-based control stops, per-territory speed limits, regen-to-battery, and the time-step loop.
- **INVARIANT: the JS must stay in sync with the Python model.** Verified to match exactly: optimized legal 3022 km / 116.2 km/h / 100% SoC; **goal-seek target-20% → 20.2% / 128.6 km/h (limit left open)**; challenger 2931.7 / 93.1 / 16.4%.
- **Goal-seek now leaves the posted speed limit open** (200 km/h analysis ceiling) so it always returns a result; any driving above NT130/SA110 is **remarked** (distance over, peak, amount over) and flagged analysis-only (§3.31.6). Applies to both the target-SoC plan and the finish-time Goal-Seek, in CLI + dashboard. **Non-goal-seek runs are unchanged and stay race-legal** (report zero exceedance).
- Controls: preset (Challenger / Optimized / **Custom** — auto-set when sliders are hand-tuned) + sliders for all car/race params, target-SoC and v-max-override toggles, a **Display→speed-table threshold** slider, and a **Goal-Seek** panel (target finish day+time → tick which non-regulation params it may tune → bisects an improvement factor and writes the found spec onto the sliders; solar 6 m² & battery 3.056 kWh are hard-excluded; reports already-met / infeasible-earliest). Outputs: summary cards, 5 charts (speed w/ substantial-change markers, SoC, power-stack, elevation, irradiance), a **per-day summary table** (SoC start/end, dist, avg speed), and the speed-profile table (units in headers; Solar-in = irr×area and Solar-act = harvested-after-efficiency columns; control-stop rows named from `data/route.csv`).
- **Sidebar and main panel scroll independently** (Preset & strategy / Goal-Seek stay visible while the main panel scrolls).

**Model facts (BWSC 2027, simulator)**
- 4-day race, Darwin→Adelaide 3022 km; regulation window 08:00–17:00; **9 location-based control stops** (30 min each, charge from solar during halt).
- **Posted speed limits NT 130 / SA 110 km/h** (§3.31.6 — no derestricted section). `--v-max` override is analysis-only (not race-legal).
- Whole-race battery strategy via `--target-soc` (calibrated by bisection in `RaceSimulator.run_to_target_soc`).
- Regen-to-battery implemented (`gravity_power` + surplus recovery); **≈0 Wh on the gentle wsc route** (verified ~62 kWh on a forced −8% slope — only matters with steeper elevation).
- Official specs: solar **6.0 m²** (§2.4.2), battery **3.056 kWh / 11 MJ** (§2.5.2). Presets: `challenger_class()` (baseline), `optimized_regulation()` (target).

**Headline engineering finding**
- At legal speed caps the `optimized_regulation` car is **solar-saturated** — at 110 km/h midday solar output exceeds demand, so the battery fills to ~100% and the surplus is **unspendable legally**. Target 20% SoC is unreachable *at legal caps* (floor 95.7%); spending the surplus requires exceeding posted limits. Goal-seek now does this automatically (leaves the limit open → target 20% reaches 20.2% at avg 128.6 km/h) and **remarks** that the plan is analysis-only, not race-legal. Design implication: the car is over-powered for legal speeds.

**File map**
- `main.py` (CLI) · `models/` (car, race) · `losses/` (10 loss models, incl. `gradient.py` `gravity_power`) · `environment/` (solar_model, atmosphere, route + `load_control_stops_km`/`load_speed_limits_km`) · `simulation/` (simulator, speed_strategy, energy_budget, plots, tables) · `index.html` (dashboard) · `data/` (route.csv, irradiance/, elevation/) · `regulations/` · `CLAUDE.md` (project instructions) · `docs/session-memory.md` (archive).
- Run examples: `python main.py --preset optimized_regulation --route wsc [--plot --table --csv] [--target-soc 0.20] [--v-max 150]`.

**Suggested next work** (from CLAUDE.md "What to Build Next"): location-based irradiance (wire `data/irradiance/`), sensitivity analysis, wind model, cloud/weather model, race strategy optimizer. (Dashboard refinement round — Goal-Seek, table/solar columns, per-day SoC, scroll & preset fixes — is **done**, merged to `main`.)

---

## Session Log (newest first)

### 2026-06-22 — Goal-seek leaves speed limit open + remarks on exceedance
#### Accomplished (branch `claude/goal-speed-limit-filter-n3pfiz`; pushed, not yet merged)
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
- Optional: merge the branch to `main` (will redeploy the dashboard). Then location-based irradiance, etc.

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
