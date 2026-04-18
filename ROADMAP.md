# Development Roadmap — FC 26 Manager Career Analytics Suite

> Target consumer: **a development AI** executing this plan autonomously.
> Reference document: [`PLAN_TECHNIQUE.md`](PLAN_TECHNIQUE.md) (hereafter **PT**).
> Schema reference: [`Structure Base de Données FC 26.md`](Structure%20Base%20de%20Données%20FC%2026.md) (hereafter **SBDD**).
> Last updated: 2026-04-18

---

## How to use this roadmap

Each sprint has:
- **Goal** — one sentence.
- **Inputs** — what must already exist.
- **Tasks** — numbered, atomic, each with concrete paths.
- **Technical guidance** — how to implement, not just what.
- **Outputs** — files / artefacts produced.
- **Done when** — acceptance checklist.
- **Dependencies** — which prior sprints must be complete.

Sprints are strictly ordered unless "can run in parallel with" is stated.

### Communication rule for the development AI

If during a sprint you encounter:
- **Missing data** (a file/value referenced here doesn't exist),
- **Unclear schema** (a column used here isn't in SBDD and isn't in a probe result),
- **Uncertain behavior** (Live Editor API call not in PT §13.2),
- **An unconfirmed method** (anything flagged in PT §15),
- **A blocker** (crash, corrupted state, irreversible choice),

then **pause the current task and ask for clarification**, citing the sprint number, task number, and the exact ambiguity. Otherwise, proceed autonomously. Do not invent API calls, do not guess column names, do not stub fields with placeholders.

### Coding conventions (apply to every sprint)

- Python 3.11+. Type-annotate all public functions.
- No `print`; use the `logging` module via `app.core.logging_setup.get_logger(__name__)`.
- No wildcard imports. No circular imports (domain must not import from ui; analytics must not import from ui or import_).
- Parsers never raise generic `Exception`; use the typed exceptions from PT §14.2.
- Lua scripts always start with `assert(IsInCM())` and wrap any §15-flagged field access in `pcall`.
- CSV writers escape `,` and `"` in string fields (`"` → `""`, wrap in quotes).

---

# PHASE A — Foundation ✅ COMPLETED (2026-04-18)

## Sprint 0 — Project Restructure (MANDATORY, FIRST) ✅ COMPLETED

**Goal**: Reorganize the repository to match PT §5 before any code is written.

**Inputs**: current repo state (SBDD, PT, `SCRIPTS/` folder, two top-level `.md` guides).

**Tasks**

1. **Create the top-level folders** exactly as in PT §5:
   - `app/` with subfolders `config/`, `core/`, `import_/`, `domain/`, `analytics/`, `ui/widgets/`, `ui/pages/`, `services/`.
   - `lua_exports/`
   - `lua_probes/`
   - `data/samples/`, `data/exports/` (add `.gitkeep` for each; add `data/exports/` to `.gitignore`).
   - `docs/`
   - `tests/`
   Each Python package directory must contain an `__init__.py` (may be empty).

2. **Migrate existing Lua scripts**:
   - Move `SCRIPTS/export_season_stats.lua` → `lua_exports/export_season_stats.lua`.
   - Move `SCRIPTS/export_fixtures.lua` → `lua_exports/export_fixtures.lua`.
   - Move `SCRIPTS/export_transfer_history.lua` → `lua_exports/export_transfer_history.lua`.
   - Leave all other `SCRIPTS/*.lua` files in `SCRIPTS/` (they are legacy references). Do **not** delete them.

3. **Create root config files**:
   - `.gitignore` — include: `__pycache__/`, `*.pyc`, `.venv/`, `build/`, `dist/`, `*.spec`, `data/exports/`, `%LOCALAPPDATA%`-equivalent cache paths, `.pytest_cache/`, `*.sqlite`, `.idea/`, `.vscode/` (settings only).
   - `requirements.txt` — pinned: `PySide6>=6.6`, `pyqtgraph>=0.13`, `pandas>=2.1`, `pytest>=8`, `pytest-qt>=4.3`. Do not add packages not listed in PT §3.2.
   - `README.md` at root — short: project name, one-sentence purpose, pointer to PT and ROADMAP. Do NOT summarize the plan.

4. **Move documentation**:
   - Leave `PLAN_TECHNIQUE.md`, `ROADMAP.md`, `Structure Base de Données FC 26.md`, `Guide des Regens FC26.md` at the root.
   - Create empty stubs (one-line title + `_To be written in a later sprint._`) for:
     - `docs/CSV_CONTRACTS.md`
     - `docs/USER_GUIDE.md`
     - `docs/SCHEMA_NOTES.md`
   - Create `lua_exports/README.md` with a one-paragraph summary of what scripts live here and the Desktop output convention from PT §13.3.

5. **Skeleton Python modules** (empty files with only a module-level docstring; do NOT implement anything yet):
   - `app/main.py`
   - `app/core/logging_setup.py`, `paths.py`, `constants.py`
   - `app/import_/discovery.py`, `schema.py`, `parsers.py`, `pipeline.py`
   - `app/domain/{player,team,league,standings,season,transfer}.py`
   - `app/analytics/{standings,form,scoring,squad,wonderkids,tactics,transfers}.py`
   - `app/ui/{app_window,theme}.py`
   - `app/ui/widgets/{stat_card,kpi_tile,sparkline,data_table,filter_bar,chart_panel}.py`
   - `app/ui/pages/{overview,analytics,squad,wonderkids,tactics,transfers,import}_page.py`
   - `app/services/{cache,export}.py`

6. **Commit strategy**: one commit — `chore: initial project restructure (Sprint 0)`.

**Done when**
- `tree -L 3 -I __pycache__` matches PT §5.
- Existing Lua exports are discoverable under `lua_exports/`.
- No Python file has implementation yet (docstrings only).
- `pytest` runs with zero collected tests and exits 0.

**Dependencies**: none.

---

## Sprint 1 — Schema Probes & Contract Finalization ✅ COMPLETED

**Goal**: Resolve every PT §15 item that can be resolved via probe scripts; freeze all CSV contracts in `docs/CSV_CONTRACTS.md`.

**Inputs**: Sprint 0 layout.

**Tasks**

1. **Write probe scripts** in `lua_probes/`. Each probe:
   - begins with `assert(IsInCM())`,
   - runs in a single pass,
   - writes a CSV to the Desktop named `PROBE_<name>_DD_MM_YYYY.csv`,
   - wraps every field read in `pcall`,
   - emits columns: `probe, status, detail, sample_value`.

   Probes to write:
   - `probe_names_integrity.lua` — for 200 sampled players, resolve `firstnameid`/`lastnameid`/`commonnameid`/`playerjerseynameid` against `playernames`; report unresolved count.
   - `probe_face_aggregates.lua` — dump `pacdiv, shohan, paskic, driref, defspe, phypos` for 20 well-known players (hard-code `playerid`s left as `TODO_ASK_USER` — **pause and ask the user** for sample IDs).
   - `probe_form_injury.lua` — histogram of `teamplayerlinks.form` and `teamplayerlinks.injury` values across all rows.
   - `probe_team_tactics.lua` — `pcall` each of `LE.db:GetTable("teamsheets")`, `"formations"`, `"teamformations"`, `"team_tactics"`; report which exist; if any succeeds, dump column list via one-row inspection.
   - `probe_objectives.lua` — dump the `objective`, `hasachievedobjective`, `highestpossible`, `highestprobable`, `yettowin`, `actualvsexpectations`, `champion` values for the user's team + 3 rival teams (rivals read via `teams.rivalteam`).
   - `probe_compobjid_mapping.lua` — emit one row per `(compobjid, compname)` from `GetPlayersStats()`, side-by-side with candidate `leagueid, leaguename` rows from `leagues`.

2. **Request probe execution**: the development AI cannot run Live Editor. **Pause and ask the user** to run the probes and place the resulting `PROBE_*.csv` files into `data/samples/probe_results/`.

3. **Write `docs/SCHEMA_NOTES.md`**: for each §15 item, record "resolved / still unknown", copying evidence from the probe CSVs. No speculation.

4. **Freeze `docs/CSV_CONTRACTS.md`**: one section per CSV kind (PT §7.1–§7.7). For each, list columns with: `name | dtype | nullable | source table.column | notes`. Do **not** add columns not in PT §7.

**Done when**
- All probe scripts exist and are statically valid (no undefined globals per PT §13.2).
- `docs/SCHEMA_NOTES.md` contains a row per §15 item with final status.
- `docs/CSV_CONTRACTS.md` is complete and matches PT §7.

**Dependencies**: Sprint 0.

---

# PHASE B — Lua Export Scripts ✅ COMPLETED (2026-04-18)

## Sprint 2 — Production Lua Exports ✅ COMPLETED

**Goal**: Implement the three new production export scripts defined in PT §13.4.

**Inputs**: Sprint 1 probes confirming names/face/form semantics (or explicit "defer" notes).

**Tasks**

1. `lua_exports/export_season_overview.lua` — implements PT §7.1. One row.
   - Read `GetUserTeamID()`.
   - Locate the user's row in `leagueteamlinks` (scan, match `teamid`).
   - Look up the `leagues` row via `leagueid`.
   - Look up the `teams` row for team-level fields.
   - Write CSV per PT §13.3.

2. `lua_exports/export_standings.lua` — implements PT §7.2.
   - Accept an optional `LEAGUE_ID` global at the top of the file; default to the user's current league.
   - Iterate `leagueteamlinks` filtering by `leagueid`, JOIN `teams` in-memory.
   - One CSV per run, filename `STANDINGS_<leaguename>_DD_MM_YYYY.csv` (sanitize name: replace non-`[A-Za-z0-9_-]` with `_`).

3. `lua_exports/export_players_snapshot.lua` — implements PT §7.3.
   - **Step 1**: full pass over `playernames`, build Lua table `NAMES[nameid] = name`.
   - **Step 2**: full pass over `teamplayerlinks`, build Lua tables keyed by `playerid` → `{teamid, jerseynumber, position, form, injury, leagueappearances, leaguegoals, leaguegoalsprevmatch, leaguegoalsprevthreematches, yellows, reds, istopscorer, isamongtopscorers, isamongtopscorersinteam}`.
   - **Step 3**: full pass over `leagueteamlinks`, build `TEAM_LEAGUE[teamid] = leagueid`.
   - **Step 4**: full pass over `leagues`, cache `(leaguename, level)`.
   - **Step 5**: full pass over `teams`, cache `teamname`.
   - **Step 6**: full pass over `players`; for each row compute `age` from `birthdate` + `GetCurrentDate()`, resolve names via `NAMES`, join team/league via caches, compute `is_generated = (playerid >= 460000)`, emit one CSV row.
   - Do NOT call `GetPlayerName` in the loop. Performance target: < 60 s for ~30k players.

4. `lua_exports/export_wonderkids.lua` — implements PT §7.4.
   - Copy `export_players_snapshot.lua` logic; in Step 6, skip rows where `age > 21` OR `potential < POTENTIAL_MIN` (constant at top, default 85).

5. Update `lua_exports/README.md`: table of `script → output filename → purpose`.

**Technical guidance**
- For display name: prefer `commonname` (if `commonnameid ~= 0`), else `firstname + " " + lastname`, else `jerseyname`.
- When a `nameid` is missing from the cache, emit empty string (never `nil`, never `"nil"`).
- Escape CSV: if a string contains `,` or `"` or newline, wrap in `"` and double any `"` inside.

**Done when**
- All four scripts exist, are statically valid, and match their §7 contracts exactly.
- A code review against SBDD confirms every column read exists on its source table.

**Dependencies**: Sprint 1.

---

# PHASE C — Python Foundation ✅ COMPLETED (2026-04-18)

## Sprint 3 — App Skeleton, Logging, Config, Paths ✅ COMPLETED

**Goal**: Python app launches an empty window with working logging and config.

**Tasks**

1. `app/core/logging_setup.py`:
   - `configure_logging(log_dir: Path) -> None` — rotating file handler (5 MB × 3) + stream handler; format `%(asctime)s %(levelname)s %(name)s %(message)s`.
   - `get_logger(name: str) -> Logger`.

2. `app/core/paths.py`:
   - `desktop_dir() -> Path` from `%USERPROFILE%\Desktop`.
   - `app_data_dir() -> Path` → `%LOCALAPPDATA%\FC26Analytics`.
   - `cache_dir()`, `log_dir()`, `config_dir()` under `app_data_dir()`.
   - Create directories on first access.

3. `app/core/constants.py`:
   - `GENERATED_PLAYER_THRESHOLD = 460000`.
   - `DEFAULT_WONDERKID_POTENTIAL = 85`.
   - `DEFAULT_WONDERKID_MAX_AGE = 21`.
   - Enum-like constants for CSV kinds: `CSVKind = Literal["season_overview", "standings", "players_snapshot", "wonderkids", "season_stats", "fixtures", "transfer_history"]`.

4. `app/config/settings.toml`:
   ```toml
   [app]
   theme = "dark"
   
   [import]
   default_scan_dir = "desktop"
   
   [wonderkids]
   min_potential = 85
   max_age = 21
   ```

5. `app/main.py`:
   - `QApplication`, read `settings.toml`, load `theme.qss`, instantiate `AppWindow`, show, `app.exec()`.
   - Wrap in `if __name__ == "__main__":`.

6. `app/ui/app_window.py`:
   - `QMainWindow` with placeholder central widget (`QLabel("FC26 Analytics — no data imported")`), sidebar `QListWidget` populated with the page names from PT §12.1 (no page routing yet), status bar showing `"Ready"`.

7. `app/config/theme.qss`: minimal dark palette (background `#0f1115`, text `#e6e8ec`, accent `#7c9cff`). Comments allowed here to name each token.

**Done when**
- `python -m app.main` opens a window. Closing it exits cleanly.
- `app.log` appears under `%LOCALAPPDATA%\FC26Analytics\logs\`.

**Dependencies**: Sprint 0.

---

## Sprint 4 — Import Pipeline & Parsers ✅ COMPLETED

**Goal**: Given a folder, detect CSV kinds, parse them, return typed dataframes with validation.

**Tasks**

1. `app/import_/schema.py`:
   - One constant per CSV kind: `SEASON_OVERVIEW_COLUMNS`, `STANDINGS_COLUMNS`, `PLAYERS_SNAPSHOT_COLUMNS`, `WONDERKIDS_COLUMNS`, `SEASON_STATS_COLUMNS`, `FIXTURES_COLUMNS`, `TRANSFER_HISTORY_COLUMNS`. Copy column lists verbatim from `docs/CSV_CONTRACTS.md`.
   - `DTYPES: dict[CSVKind, dict[str, str]]` with explicit pandas dtypes (IDs → `"Int64"`, booleans → `"boolean"`, names → `"string"`).
   - `REQUIRED_COLUMNS: dict[CSVKind, frozenset[str]]` — IDs and primary keys mandatory; attribute columns optional.

2. `app/import_/discovery.py`:
   - `detect_kind(filename: str) -> CSVKind | None` using regex on the PT §6.1 patterns.
   - `scan(folder: Path) -> list[DetectedFile]` where `DetectedFile(path, kind, export_date)`.

3. `app/import_/parsers.py`:
   - `BaseParser` with `parse(path: Path) -> ParsedCSV` (dataclass `ParsedCSV(df: pd.DataFrame, kind: CSVKind, export_date: date, source_filename: str, rows_read: int, rows_dropped: int, warnings: list[str])`).
   - One subclass per kind. Each: reads CSV with explicit dtypes, validates required columns, coerces dates (birthdate etc.), returns `ParsedCSV`.
   - Typed exceptions: `MissingColumnError(kind, columns)`, `SchemaMismatchError(...)`, `EmptyFileError(path)`.

4. `app/import_/pipeline.py`:
   - `import_folder(folder: Path) -> ImportReport` orchestrates discovery → per-file parse → report.
   - `ImportReport(files: list[FileReport], totals: dict)` where `FileReport(path, kind, status, rows_read, rows_dropped, error)`.
   - Non-fatal warnings collected; fatal errors recorded per-file, never raised to caller.

5. `tests/test_parsers.py`:
   - Use tiny synthetic CSVs in `data/samples/` for each kind (the development AI may author these using the frozen column contracts).
   - Assert row counts, dtypes, required-column enforcement.

**Technical guidance**
- Prefer `pd.read_csv(path, dtype=DTYPES[kind], na_values=["", "nil"], keep_default_na=True)`.
- Dates: keep raw int column AND add `<col>_dt` via helper `gregorian_days_to_date(days)` (FC26 Gregorian-day epoch is 0001-01-01 — confirm when writing the helper; if uncertain, **pause and ask**).
- Never mutate the input path's file.

**Done when**
- `pytest tests/test_parsers.py` passes for all 7 kinds.
- `import_folder(data/samples)` returns a report with `status == "ok"` for every synthetic sample.

**Dependencies**: Sprint 3.

---

## Sprint 5 — Domain Model & Session Cache ✅ COMPLETED

**Goal**: Dataframes → typed domain objects; persist to SQLite; reload without re-parsing.

**Tasks**

1. `app/domain/*.py` — dataclasses matching the CSV contracts. Fields are typed primitives; no pandas references. Examples:
   - `Player` — all §7.3 fields.
   - `StandingsRow` — §7.2.
   - `SeasonOverview` — §7.1.
   - `League`, `Team` extracted where relevant.
   - Each module exposes `from_dataframe(df) -> list[T]`.

2. `app/services/cache.py`:
   - `SessionCache(path: Path)` wrapping `sqlite3`.
   - Tables: `imports(kind, export_date, source_filename, imported_at, row_count)` and `rows_<kind>` (raw columns from the CSV).
   - `save(parsed: ParsedCSV)`, `load_latest(kind) -> DataFrame | None`, `list_snapshots(kind) -> list[date]`, `load_snapshot(kind, date)`.
   - File naming: `cache_dir() / f"{career_slug}.sqlite"` — `career_slug` supplied by caller.

3. `tests/test_cache.py`: round-trip a synthetic ParsedCSV and assert equality.

**Done when**
- Round-trip tests pass for every CSV kind.
- Two imports of the same kind on different dates produce two separate rows in `imports`.

**Dependencies**: Sprint 4.

---

# PHASE D — Analytics

## Sprint 6 — Standings & Form Analytics

**Goal**: Implement PT §9.1 + §9.2.

**Tasks**

1. `app/analytics/standings.py`:
   - `points_progression(standings_history: list[StandingsRow]) -> Series` — requires multi-snapshot; gracefully returns empty if only one snapshot.
   - `gf_ga_home_away_split(row: StandingsRow) -> dict`.
   - `goal_difference(row: StandingsRow) -> int`.

2. `app/analytics/form.py`:
   - `decode_team_form(teamform: str | int) -> list[Literal["W","D","L"]]` — encoding resolved per Sprint 1 probe.
   - `current_streak(results: list[str]) -> Streak`.
   - `longest_unbeaten(results: list[str]) -> int` (also derivable from `unbeatenleague`; prefer the direct field when available, fall back to computed).

3. `tests/test_analytics_standings.py`, `test_analytics_form.py`: cover each public function.

**Done when**: tests pass, public API is pure functions with no Qt / IO deps.

**Dependencies**: Sprint 5.

---

## Sprint 7 — Squad, Wonderkids, Transfers Analytics

**Goal**: Implement PT §9.3, §9.4, §9.5, §9.7.

**Tasks**

1. `app/analytics/squad.py`:
   - `top_scorers(players: DataFrame, n=10)` uses `leaguegoals`; tiebreak by `overallrating`.
   - `top_by_rating(players, n=10, position_group=None)`.
   - `injury_list(players)` filters `injury > 0` (scale semantics per Sprint 1 probe).
   - `form_leaders(players, n=10)` top by `form`.

2. `app/analytics/wonderkids.py`:
   - `filter_wonderkids(players, max_age=21, min_potential=85)`.
   - `origin_label(playerid) -> Literal["real","generated"]` using `GENERATED_PLAYER_THRESHOLD`.
   - `position_group(pos: str) -> Literal["GK","DEF","MID","ATT"]` — map from `preferredposition1` values.

3. `app/analytics/transfers.py`:
   - `aging_quadrant(players)` returns `(age, overallrating, name, teamid)` tuples.
   - `expiring_contracts(players, current_year)` filters `contractvaliduntil <= current_year + 1`.
   - `positional_depth(players, teamid)` counts players per `preferredposition1`.
   - `replacement_candidates(players, target_player, top_n=10)`: same primary position, younger, OVR ≥ target.OVR − 3 OR potential ≥ target.potential − 2.

4. `app/analytics/tactics.py`:
   - `team_ratings_profile(overview: SeasonOverview) -> dict` — overall/attack/mid/defense + matchday counterparts.
   - `home_away_efficiency(row: StandingsRow) -> dict` — GF/match, GA/match, clean-sheet proxy.

5. `app/analytics/scoring.py`: monthly GF/GA aggregation (requires FIXTURES_* — gate with presence check).

6. Tests for each module with minimal fixture dataframes.

**Done when**: all tests pass; every analytics function is pure.

**Dependencies**: Sprint 6.

---

# PHASE E — UI

## Sprint 8 — UI Shell, Theme, Base Widgets

**Goal**: Shell with working sidebar routing + reusable widget primitives.

**Tasks**

1. `app/ui/theme.py`: `Palette`, `Spacing`, `Radii`, `FontTokens` dataclasses. Expose `load_qss(palette) -> str`.

2. `app/ui/app_window.py`: replace placeholder with `QStackedWidget` wired to sidebar; one page per PT §12.2 entry (pages can be `QLabel(page_name)` placeholders for now).

3. Widgets (each in its own file under `app/ui/widgets/`):
   - `stat_card.py` — `StatCard(title, value, subtitle=None, trend: Sparkline | None)`.
   - `kpi_tile.py` — `KpiTile(label, value, delta=None)`.
   - `sparkline.py` — `Sparkline(values: list[float], color)` (PyQtGraph).
   - `data_table.py` — `DataTable(df: DataFrame, columns=None)` wrapping `QTableView` + a pandas model.
   - `filter_bar.py` — composable `QToolBar` with search + combos.
   - `chart_panel.py` — `ChartPanel(title, subtitle, x_axis, y_axis, series[])` wrapping PyQtGraph's `PlotWidget`.

4. `tests/test_pages_smoke.py`: with `pytest-qt`, instantiate each widget with a trivial input and assert no exception.

**Done when**: sidebar routes; all widgets render in a demo harness script under `tests/manual/demo_widgets.py`.

**Dependencies**: Sprint 3 (shell) + Sprint 7 (for later binding — not blocking).

---

## Sprint 9 — Overview & Analytics Pages

**Goal**: Bind real data to the first two pages.

**Tasks**

1. `app/ui/pages/overview_page.py`:
   - Hero: club name + season label + league + current position.
   - KPI grid: Points, W, D, L, GF, GA, GD, Recent Form (5 dots from `teamshortform`), Objective progress (`hasachievedobjective` + `actualvsexpectations` text).
   - Each KPI uses `StatCard` + `Sparkline` (sparkline only present if multi-snapshot data exists).

2. `app/ui/pages/analytics_page.py`:
   - Grid of `ChartPanel`s: points progression, ranking evolution (inverted Y), home vs away GF/GA (stacked bar), form curve (line from `teamlongform` decoding), streaks panel (text + color coded using `unbeaten*`).

3. ViewModel layer (keep in the page file unless it grows >150 lines; then split into `app/ui/viewmodels/`): page calls a `build_overview_vm(cache)` function that returns a plain dataclass ready for rendering.

**Done when**: loading a real `SEASON_OVERVIEW` CSV via Import page (stub file picker for now) renders the Overview page end-to-end with no runtime errors.

**Dependencies**: Sprint 5, Sprint 7, Sprint 8.

---

## Sprint 10 — Squad & Wonderkids Pages

**Tasks**

1. `squad_page.py`:
   - Filter bar (competition, position, min minutes — stub if `SEASON_STATS` not imported).
   - Leaderboards (horizontal bar charts): top scorers, assists, appearances, ratings, clean sheets.
   - Per-player drawer (`QDockWidget` on the right): radar of 6 attribute groups (use the raw 6×summed groupings if `pacdiv`..`phypos` encoding unresolved), attribute list, form/injury badges.

2. `wonderkids_page.py`:
   - Table sorted by potential desc.
   - Quadrant scatter (age × potential), colored by `position_group`.
   - Origin badge column (real/generated).
   - Per-player drawer shared with squad page.

**Done when**: both pages render with a realistic sample snapshot (≥5000 players) in under 2 seconds.

**Dependencies**: Sprint 9.

---

## Sprint 11 — Tactics & Transfers Pages

**Tasks**

1. `tactics_page.py`:
   - Team ratings gauges (overall/attack/mid/defense + matchday variants).
   - `buildupplay` + `defensivedepth` as labeled dials.
   - Home vs away efficiency bars.
   - Formation pitch visual: **gated** on Sprint 1 §15.4 resolution; if unresolved, render a "Formation data unavailable in this build" placeholder card.

2. `transfers_page.py`:
   - Aging quadrant (scatter age × OVR).
   - Expiring contracts table (years-left derived from `contractvaliduntil - current_season_year`).
   - Replacement finder: select a player → right-pane ranked candidates from `replacement_candidates`.
   - Positional depth bar chart.
   - `numtransfersin` KPI at the top.

**Done when**: both pages render; placeholder cards are explicit about what's missing and why.

**Dependencies**: Sprint 10.

---

## Sprint 12 — Import Page, Polish, Packaging

**Tasks**

1. `import_page.py`:
   - Drag-and-drop zone (`QWidget` with `acceptDrops=True`).
   - File picker fallback.
   - Detected files list with status icons (ok / warning / error).
   - Parse log (monospace `QPlainTextEdit`, read-only).
   - "Clear cache" control → confirm dialog → `SessionCache.clear()`.

2. Wire the app-wide import flow:
   - User picks folder (default `desktop_dir()`).
   - `pipeline.import_folder(folder)` runs in a `QThreadPool` worker.
   - Results pushed to `SessionCache`; pages invalidated via a global signal.

3. Theme polish: light-mode toggle, hover states, consistent spacing, verify readability at 125% Windows DPI scaling.

4. Packaging:
   - `pyinstaller` spec under `packaging/fc26_analytics.spec`.
   - One-file `.exe` target, windowed (no console).
   - Include `app/config/` and `app/ui/` static assets.
   - Build script `packaging/build.ps1`.

**Done when**: a fresh build of the `.exe` launches, imports a Desktop export, and renders all pages without errors.

**Dependencies**: Sprint 11.

---

## Sprint 13 — Testing, QA, Documentation

**Tasks**

1. Fill gaps in unit tests; target ≥70 % coverage of `app/analytics/` and `app/import_/`.
2. Add a `pytest-qt` smoke test per page that loads the sample snapshot and asserts no uncaught Qt warnings.
3. `docs/USER_GUIDE.md`:
   - How to run the Lua exports.
   - Where CSVs land.
   - How to import them.
   - Page-by-page walkthrough with one screenshot per page (development AI may leave `TODO_SCREENSHOT` markers for the user).
4. `lua_exports/README.md` final version with script list, params, expected CSV names.
5. Verify all "TODO_ASK_USER" markers in the codebase are resolved.

**Done when**: CI (if configured) or `pytest -q` passes locally; `docs/USER_GUIDE.md` is complete.

**Dependencies**: Sprint 12.

---

# Cross-sprint rules

1. **No feature creep**: anything not in PT is out of scope. If tempted to add a feature, write it into a `docs/FUTURE.md` instead.
2. **No speculative columns**: every CSV column must trace back to SBDD or an API-confirmed source (PT §4.7 exceptions).
3. **No Lua API invention**: only methods listed in PT §13.2 may be called.
4. **One sprint at a time**: do not start Sprint N+1 before Sprint N is "Done when".
5. **Traceability**: every commit message cites the sprint and task, e.g. `feat(s4.t3): parsers for SEASON_OVERVIEW + STANDINGS`.
6. **Pause-and-ask** whenever the Communication rule at the top applies — do not silently substitute assumptions.

---

*End of roadmap.*
