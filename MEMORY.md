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
- **INVARIANT: the JS must stay in sync with the Python model.** Verified to match exactly: optimized legal 3022 km / 116.2 km/h / 100% SoC; legal target-20% floor 95.7%; `--v-max 150` target-20% → 20.2%; challenger 2931.7 / 93.1 / 16.4%.
- Controls: preset (Challenger/Optimized) + sliders for all car/race params, plus target-SoC and v-max-override toggles. Outputs: summary cards, 5 charts (speed, SoC, power-stack, elevation, irradiance), and a speed-profile table.

**Model facts (BWSC 2027, simulator)**
- 4-day race, Darwin→Adelaide 3022 km; regulation window 08:00–17:00; **9 location-based control stops** (30 min each, charge from solar during halt).
- **Posted speed limits NT 130 / SA 110 km/h** (§3.31.6 — no derestricted section). `--v-max` override is analysis-only (not race-legal).
- Whole-race battery strategy via `--target-soc` (calibrated by bisection in `RaceSimulator.run_to_target_soc`).
- Regen-to-battery implemented (`gravity_power` + surplus recovery); **≈0 Wh on the gentle wsc route** (verified ~62 kWh on a forced −8% slope — only matters with steeper elevation).
- Official specs: solar **6.0 m²** (§2.4.2), battery **3.056 kWh / 11 MJ** (§2.5.2). Presets: `challenger_class()` (baseline), `optimized_regulation()` (target).

**Headline engineering finding**
- At legal speed caps the `optimized_regulation` car is **solar-saturated** — at 110 km/h midday solar output exceeds demand, so the battery fills to ~100% and the surplus is **unspendable legally**. Target 20% SoC is unreachable (floor 95.7%); reaching 20% needs illegal speed (`--v-max 150` → 20.2%, avg 128.6 km/h). Design implication: the car is over-powered for legal speeds.

**File map**
- `main.py` (CLI) · `models/` (car, race) · `losses/` (10 loss models, incl. `gradient.py` `gravity_power`) · `environment/` (solar_model, atmosphere, route + `load_control_stops_km`/`load_speed_limits_km`) · `simulation/` (simulator, speed_strategy, energy_budget, plots, tables) · `index.html` (dashboard) · `data/` (route.csv, irradiance/, elevation/) · `regulations/` · `CLAUDE.md` (project instructions) · `docs/session-memory.md` (archive).
- Run examples: `python main.py --preset optimized_regulation --route wsc [--plot --table --csv] [--target-soc 0.20] [--v-max 150]`.

**Suggested next work** (from CLAUDE.md "What to Build Next"): refine the dashboard (current intent); then location-based irradiance (wire `data/irradiance/`), sensitivity analysis, wind model, cloud/weather model, race strategy optimizer.

---

## Session Log (newest first)

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
