# Technical Plan — FC 26 Manager Career Analytics Suite

> Master technical document for the new project direction.
> Supersedes `PLAN_TECHNIQUE_REGEN_DETECTOR.md` (the clone-detection project is retired — retiring players are removed from the DB before comparisons are possible).
> Last updated: 2026-04-17
> Status: **Planning only — no implementation yet.**
> Major revision: schema grounded in the manually-verified [`Structure Base de Données FC 26.md`](Structure%20Base%20de%20Données%20FC%2026.md) (hereafter **SBDD**).

---

## 1. Project Vision

Build a **Python desktop analytics and scouting utility for EA Sports FC 26 Manager Career Mode**, delivering a polished seasonal intelligence dashboard to the user.

### Core principles

- **Offline-first**: the desktop app never touches the game. It reads only CSV files exported by a dedicated Lua script.
- **Ergonomic UI/UX**: modern, polished, readable, intuitive. UI quality is a first-class requirement.
- **Visual analytics**: prioritize charts, trends, and at-a-glance summaries over raw tables.
- **Deterministic**: same CSV input → same dashboards. No hidden state, no network calls.
- **Seasonal focus**: the app models a career-mode season (league position, form, transfers, youth intake) end-to-end.

### Non-goals

- Real-time integration with the live game.
- Direct Live Editor execution from Python.
- Regen clone detection (abandoned direction).
- Cloud sync, multi-user, or online services.

---

## 2. End-to-End Workflow

```
[1] User launches FC 26
[2] User opens Live Editor
[3] User runs our dedicated Lua export script(s)
[4] Script writes CSV file(s) to the Desktop
[5] User launches the Python desktop app (PySide6)
[6] User imports the CSV(s) via the UI
[7] App parses, indexes, and builds dashboards
[8] User explores Overview / Analytics / Squad / Wonderkids / Tactics / Transfers
```

The Python app is a **pure CSV consumer**.

---

## 3. Software Architecture

### 3.1 High-level layering

```
┌──────────────────────────────────────────────────────┐
│  UI Layer (PySide6)                                  │
├──────────────────────────────────────────────────────┤
│  Presentation / ViewModel Layer                      │
├──────────────────────────────────────────────────────┤
│  Analytics Engine                                    │
├──────────────────────────────────────────────────────┤
│  Domain Model                                        │
├──────────────────────────────────────────────────────┤
│  Import / Parsing Pipeline                           │
├──────────────────────────────────────────────────────┤
│  Persistence / Cache (SQLite)                        │
└──────────────────────────────────────────────────────┘
```

### 3.2 Technology stack

| Layer | Choice |
|-------|--------|
| UI framework | **PySide6** (Qt 6) |
| Charts | **PyQtGraph** primary, **QtCharts** fallback |
| Data handling | **pandas** (polars optional later) |
| CSV parsing | `pandas.read_csv` with explicit dtypes |
| Persistence / cache | **SQLite** (`sqlite3`) |
| Packaging | **PyInstaller** (decision locked — simpler one-file target for Windows) |
| Config | TOML via `tomllib` (stdlib, Python 3.11+) |
| Logging | `logging` stdlib, rotating file handler |
| Testing | `pytest`, `pytest-qt` |

### 3.3 Threading model

- UI on the main thread only.
- Imports and heavy aggregations run on `QThreadPool`.
- Qt signals publish progress/results back to the UI.

---

## 4. Confirmed Database Schema (from SBDD)

This section is the **source of truth** for all schema references in this plan. Every column name here is copied verbatim from SBDD.

### 4.1 `players` (154 columns confirmed)

Grouped for this plan:

**Identity / naming**
- `playerid` — PK. `>= 460000` = generated, `< 460000` = real (DB).
- `firstnameid`, `lastnameid`, `commonnameid`, `playerjerseynameid` — foreign keys into **`playernames.nameid`**.
- `birthdate` — Gregorian-day integer. Age = f(birthdate, `GetCurrentDate()`).
- `gender`, `nationality`.
- `isretiring`, `iscustomized`, `usercaneditname`, `hasseasonaljersey`.

**Positions & roles**
- `preferredposition1` … `preferredposition7` (all confirmed present).
- `role1` … `role5` (squad roles / playstyle roles).
- `preferredfoot`.

**Ratings & attributes (core)**
- Global: `overallrating`, `potential`, `internationalrep`.
- GK: `gkdiving`, `gkhandling`, `gkkicking`, `gkpositioning`, `gkreflexes`, `gksavetype`, `gkkickstyle`, `gkglovetypecode`.
- ATT: `crossing`, `finishing`, `headingaccuracy`, `shortpassing`, `volleys`.
- DEF: `defensiveawareness`, `standingtackle`, `slidingtackle`.
- SKL: `dribbling`, `curve`, `freekickaccuracy`, `longpassing`, `ballcontrol`.
- PWR: `shotpower`, `jumping`, `stamina`, `strength`, `longshots`.
- MOV: `acceleration`, `sprintspeed`, `agility`, `reactions`, `balance`.
- MEN: `aggression`, `composure`, `interceptions`, `positioning`, `vision`, `penalties`.
- Face/stat aggregates (likely the 6 front-face attributes, encoding TBD via probe): `pacdiv`, `shohan`, `paskic`, `driref`, `defspe`, `phypos`.

**Playstyles / traits**
- `trait1`, `trait2`, `icontrait1`, `icontrait2`.
- `skillmoves`, `skillmoveslikelihood`, `weakfootabilitytypecode`.

**Contract (inline on players)**
- `contractvaliduntil`, `playerjointeamdate`.

**Physical / cosmetic (most not used by analytics but preserved)**
- `height`, `weight`, `bodytypecode`, `muscularitycode`, `headvariation`, `facepsdlayer0`, `facepsdlayer1`, `faceposerpreset`, `headtypecode`, `headclasscode`, `headassetid`, `hashighqualityhead`.
- Hair / face / tattoo / skin / jersey / shoe / accessory fields (ignored by analytics).

**Not present in `players`** (critical — do not invent):
- No `age` column.
- No `firstname` / `lastname` / `commonname` as strings (must JOIN via `playernames`).
- No `injury` / `form` / `fitness` / `morale` / `sharpness` on `players` (see 4.3).
- No per-match shot / pass / xG telemetry.

### 4.2 `playernames` (name dictionary)

- `nameid` (PK)
- `commentaryid`
- `name` (string, e.g. `"A. Abqar"`)

**Join rule**: resolve display name as `COALESCE(commonname, "firstname + lastname", playerjerseyname)` by joining `players.{firstnameid,lastnameid,commonnameid,playerjerseynameid}` → `playernames.nameid`.

### 4.3 `teamplayerlinks` (player↔team relation and in-season stats)

All columns: `artificialkey` (PK), `teamid`, `playerid`, `jerseynumber`, `position`, `form`, `injury`, `leagueappearances`, `leaguegoals`, `leaguegoalsprevmatch`, `leaguegoalsprevthreematches`, `yellows`, `reds`, `isamongtopscorers`, `isamongtopscorersinteam`, `istopscorer`.

**Impact on plan**:
- Current club assignment: `(teamid, playerid)`.
- `position` here is the **effective squad position** (distinct from `preferredposition*` on `players`).
- `form` and `injury` are **per-player** and live here, not on `players`. This **resolves Points to Verify 16.1 injury/form**.
- League goals/appearances are on this table, **not** on `players`.

### 4.4 `leagues`

`leagueid` (PK), `leaguename`, `countryid`, `level`, `leaguetype`, `leaguetimeslice`, `isinternationalleague`, `iswomencompetition`, `iswithintransferwindow`, plus competition-presentation flags (`iscompetitioncrowdcardsenabled`, `iscompetitionscarfenabled`, `iscompetitionpoleflagenabled`, `isbannerenabled`).

### 4.5 `leagueteamlinks` (standings row)

`artificialkey` (PK), `leagueid`, `teamid`, `prevleagueid`, `grouping`.

**Standings counters**: `points`, `currenttableposition`, `previousyeartableposition`, `nummatchesplayed`, `homewins`, `homedraws`, `homelosses`, `awaywins`, `awaydraws`, `awaylosses`, `homegf`, `homega`, `awaygf`, `awayga`.

**Form signals**: `teamform`, `teamshortform`, `teamlongform`, `lastgameresult`, `unbeatenhome`, `unbeatenaway`, `unbeatenleague`, `unbeatenallcomps`.

**Objectives**: `objective`, `hasachievedobjective`, `highestpossible`, `highestprobable`, `yettowin`, `actualvsexpectations`, `champion`.

**Impact**: full standings are available for every team, not just the user's. GF/GA split home/away enables rich defensive/attacking charts.

### 4.6 `teams` (club reference + team-level aggregates)

**Identity**: `teamid` (PK), `teamname`, `assetid`, `foundationyear`, `cityid`, `latitude`, `longitude`, `utcoffset`.

**Team ratings**: `overallrating`, `attackrating`, `midfieldrating`, `defenserating`, `matchdayoverallrating`, `matchdayattackrating`, `matchdaymidfieldrating`, `matchdaydefenserating`, `form`.

**Tactical (newly confirmed)**: `buildupplay`, `defensivedepth`.

**Key players**: `captainid`, `penaltytakerid`, `freekicktakerid`, `leftfreekicktakerid`, `rightfreekicktakerid`, `leftcornerkicktakerid`, `rightcornerkicktakerid`, `longkicktakerid`.

**Corner-support plan**: `cksupport1` … `cksupport9` (attacker-movement flags on corners).

**Prestige / honours**: `internationalprestige`, `domesticprestige`, `popularity`, `clubworth`, `profitability`, `youthdevelopment`, `leaguetitles`, `domesticcups`, `uefa_cl_wins`, `uefa_el_wins`, `uefa_uecl_wins`, `uefa_consecutive_wins`, `prev_el_champ`.

**Matchup bias**: `trait1vstrong`, `trait1vweak`, `trait1vequal`, `opponentstrongthreshold`, `opponentweakthreshold`, `rivalteam`.

**Formation pointer**: `favoriteteamsheetid` — **not yet resolved** to a concrete `teamsheets`/`formations` table (see §16.3).

**Stadium / cosmetics**: `teamstadiumcapacity`, `stadiummowpattern_code`, `stadiumgoalnetpattern`, `stadiumgoalnetstyle`, `pitchcolor`, `pitchlinecolor`, `pitchwear`, `playsurfacetype`, `hasstandingcrowd`, `hastifo`, `hasvikingclap`, `hassubstitutionboard`, `hassuncanthem`, `haslargeflag`, `skinnyflags`, banner / flag / crowd flags, team colors (`teamcolor1r/g/b`, `teamcolor2r/g/b`, `teamcolor3r/g/b`), `goalnetstanchioncolor1r/g/b`, `goalnetstanchioncolor2r/g/b`, `genericbanner`, `genericint1`, `genericint2`, `jerseytype`, `ballid`, `presassetone`, `presassettwo`, `cornerflagpolecolor`, `flamethrowercannon`, `stanchionflamethrower`, `throwerleft`, `throwerright`, `crowdskintonecode`, `crowdregion`, `trainingstadium`, `ethnicity`, `gender`, `personalityid`, `powid`.

**Transfers**: `numtransfersin`.

### 4.7 Tables still relied on but **not present in SBDD** (carry over from prior plan)

These were previously confirmed at the Lua-API level but are **not** in the manually-verified document. They remain tentatively usable, flagged as "API-confirmed, not SBDD-confirmed":

- `career_playercontract` — `playerid`, `contract_status`, `contract_date`, `last_status_change_date`, `duration_months`, `playerrole`. (Used by `extend_user_team_players_contracts.lua`.)
- Memory-only structures for fixtures / transfer history / negotiations (see `export_fixtures.lua`, `export_transfer_history.lua`).

---

## 5. Folder / Module Structure

```
<project-root>/
├── app/                              # Python desktop application
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── settings.toml
│   │   └── theme.qss
│   ├── core/
│   │   ├── logging_setup.py
│   │   ├── paths.py
│   │   └── constants.py              # Column names, enums, thresholds
│   ├── import_/
│   │   ├── discovery.py
│   │   ├── schema.py                 # One schema per CSV kind (SBDD-grounded)
│   │   ├── parsers.py
│   │   └── pipeline.py
│   ├── domain/
│   │   ├── player.py
│   │   ├── team.py
│   │   ├── league.py
│   │   ├── standings.py
│   │   ├── season.py
│   │   └── transfer.py
│   ├── analytics/
│   │   ├── standings.py
│   │   ├── form.py
│   │   ├── scoring.py
│   │   ├── squad.py
│   │   ├── wonderkids.py
│   │   ├── tactics.py
│   │   └── transfers.py
│   ├── ui/
│   │   ├── app_window.py
│   │   ├── theme.py
│   │   ├── widgets/
│   │   │   ├── stat_card.py
│   │   │   ├── kpi_tile.py
│   │   │   ├── sparkline.py
│   │   │   ├── data_table.py
│   │   │   ├── filter_bar.py
│   │   │   └── chart_panel.py
│   │   └── pages/
│   │       ├── overview_page.py
│   │       ├── analytics_page.py
│   │       ├── squad_page.py
│   │       ├── wonderkids_page.py
│   │       ├── tactics_page.py
│   │       ├── transfers_page.py
│   │       └── import_page.py
│   └── services/
│       ├── cache.py
│       └── export.py
│
├── lua_exports/                      # Production export scripts
│   ├── README.md
│   ├── export_season_overview.lua
│   ├── export_players_snapshot.lua
│   ├── export_wonderkids.lua
│   ├── export_season_stats.lua       # (moved from SCRIPTS/)
│   ├── export_fixtures.lua           # (moved from SCRIPTS/)
│   └── export_transfer_history.lua   # (moved from SCRIPTS/)
│
├── lua_probes/                       # Throwaway probe / discovery scripts
│   ├── probe_face_aggregates.lua
│   ├── probe_team_tactics.lua
│   ├── probe_objectives.lua
│   └── probe_compobjid_mapping.lua
│
├── SCRIPTS/                          # Legacy helpers, reference-only
│
├── data/
│   ├── samples/                      # Sample CSVs for tests/dev
│   └── exports/                      # (gitignored) user's Desktop exports
│
├── docs/
│   ├── CSV_CONTRACTS.md
│   ├── USER_GUIDE.md
│   └── SCHEMA_NOTES.md               # Derived notes on SBDD
│
├── tests/
│   ├── test_parsers.py
│   ├── test_analytics_*.py
│   └── test_pages_smoke.py
│
├── Structure Base de Données FC 26.md
├── Guide des Regens FC26.md
├── PLAN_TECHNIQUE.md
├── ROADMAP.md
└── requirements.txt
```

---

## 6. Data Flow

```
Lua export scripts  ──►  CSV files on Desktop
                              │
                              ▼
                     [ Import pipeline ]
                              │
                              ▼
                  [ Domain model objects ]
                              │
                              ▼
                    [ Analytics engine ]
                              │
                              ▼
            [ ViewModels (Qt-friendly shapes) ]
                              │
                              ▼
                       [ UI pages ]
```

Rules:
- Parsers never know about the UI.
- Analytics never know about CSV formats.
- UI never reads CSVs directly.

---

## 7. CSV Contracts (SBDD-grounded)

Every CSV kind below has a frozen column list. Extra columns are tolerated; missing required columns error.

### 7.1 `SEASON_OVERVIEW_DD_MM_YYYY.csv`

**Source (Lua)**: `leagueteamlinks` (filtered to user team) + `leagues` + `teams`.
**One row per (user team × current league)**.

Columns:
```
export_date, season_year,
user_teamid, user_teamname,
leagueid, leaguename, league_level, leaguetype,
currenttableposition, previousyeartableposition,
points, nummatchesplayed,
homewins, homedraws, homelosses, awaywins, awaydraws, awaylosses,
homegf, homega, awaygf, awayga,
teamform, teamshortform, teamlongform, lastgameresult,
unbeatenhome, unbeatenaway, unbeatenleague, unbeatenallcomps,
objective, hasachievedobjective, highestpossible, highestprobable,
yettowin, actualvsexpectations, champion,
team_overallrating, team_attackrating, team_midfieldrating, team_defenserating,
buildupplay, defensivedepth,
captainid, penaltytakerid, freekicktakerid,
leftcornerkicktakerid, rightcornerkicktakerid,
longkicktakerid, leftfreekicktakerid, rightfreekicktakerid,
favoriteteamsheetid,
teamstadiumcapacity, clubworth, domesticprestige, internationalprestige
```

### 7.2 `STANDINGS_<league>_DD_MM_YYYY.csv`

**Source**: `leagueteamlinks` WHERE `leagueid = <league>` JOIN `teams`.
**One row per team in the league.**

Columns:
```
export_date, leagueid, leaguename, teamid, teamname,
currenttableposition, previousyeartableposition, points, nummatchesplayed,
homewins, homedraws, homelosses, awaywins, awaydraws, awaylosses,
homegf, homega, awaygf, awayga,
teamform, teamlongform, lastgameresult,
unbeatenleague, champion,
team_overallrating
```

### 7.3 `PLAYERS_SNAPSHOT_DD_MM_YYYY.csv`

**Source**: full pass over `players`, JOIN `teamplayerlinks` on `playerid`, JOIN `teams` on `teamid`, JOIN `leagueteamlinks` to find `leagueid`, JOIN `playernames` ×4 for names.

One row per player.

Columns (frozen):
```
export_date,
playerid, is_generated,
firstname, lastname, commonname, display_name, jerseyname,
birthdate, age, nationality, gender,
preferredfoot,
preferredposition1, preferredposition2, preferredposition3,
preferredposition4, preferredposition5, preferredposition6, preferredposition7,
role1, role2, role3, role4, role5,
overallrating, potential, internationalrep,
pacdiv, shohan, paskic, driref, defspe, phypos,
# GK
gkdiving, gkhandling, gkkicking, gkpositioning, gkreflexes,
# ATT
crossing, finishing, headingaccuracy, shortpassing, volleys,
# DEF
defensiveawareness, standingtackle, slidingtackle,
# SKL
dribbling, curve, freekickaccuracy, longpassing, ballcontrol,
# PWR
shotpower, jumping, stamina, strength, longshots,
# MOV
acceleration, sprintspeed, agility, reactions, balance,
# MEN
aggression, composure, interceptions, positioning, vision, penalties,
trait1, trait2, icontrait1, icontrait2,
skillmoves, skillmoveslikelihood, weakfootabilitytypecode,
height, weight,
contractvaliduntil, playerjointeamdate,
isretiring,
# club + league (from teamplayerlinks → teams → leagueteamlinks)
teamid, teamname, jerseynumber, squad_position,
leagueid, leaguename, league_level,
# per-team in-season stats
form, injury,
leagueappearances, leaguegoals,
leaguegoalsprevmatch, leaguegoalsprevthreematches,
yellows, reds,
istopscorer, isamongtopscorers, isamongtopscorersinteam
```

Notes:
- `display_name` is resolved in Lua (prefer `commonname` → `firstname + " " + lastname` → `jerseyname`).
- `age` is computed in Lua from `birthdate` and `GetCurrentDate()`.
- `is_generated` = `playerid >= 460000`.

### 7.4 `WONDERKIDS_DD_MM_YYYY.csv`

Same columns as PLAYERS_SNAPSHOT **filtered** to `age <= 21 AND potential >= POTENTIAL_MIN` (default 85, parameterized).

### 7.5 `SEASON_STATS_DD_MM_YYYY.csv` (existing)

Unchanged. Columns per `export_season_stats.lua`: `playerid, app, goals, assists, yellow, two_yellow, red, saves, goals_conceded, clean_sheets, motm, avg, compobjid, compname`.

### 7.6 `FIXTURES_<competition>_DD_MM_YYYY.csv` (existing)

Unchanged (memory-sourced).

### 7.7 `TRANSFER_HISTORY_DD_MM_YYYY.csv` (existing)

Unchanged (memory-sourced).

---

## 8. Parsing Engine Details

One parser per CSV kind. Each returns `ParsedCSV(df, metadata)` where metadata carries `season`, `export_date`, `source_filename`, `kind`.

| Parser | Source CSV | Produces |
|--------|-----------|----------|
| `parse_season_overview` | SEASON_OVERVIEW | Club + league + standings row (user team) |
| `parse_standings` | STANDINGS_* | Full league table |
| `parse_players_snapshot` | PLAYERS_SNAPSHOT | Player table |
| `parse_wonderkids` | WONDERKIDS | Filtered player table |
| `parse_season_stats` | SEASON_STATS | Per-player per-competition stats |
| `parse_fixtures` | FIXTURES_* | Fixtures per competition |
| `parse_transfer_history` | TRANSFER_HISTORY | Transfers + loans |

All parsers share a base `BaseParser.parse(path) -> ParsedCSV`.

Type-coercion rules:
- IDs → `Int64` (nullable).
- Dates (`birthdate`, `playerjointeamdate`, `contractvaliduntil`) kept as raw ints AND as a `datetime64` sibling column.
- Names → `string` dtype.
- Booleans (`isretiring`, `champion`, `istopscorer`, …) → `bool`.

---

## 9. Analytics Engine

### 9.1 Standings & season progression
Inputs: SEASON_OVERVIEW + STANDINGS_* (+ FIXTURES_* if available).
Outputs: points-per-matchday, position-per-matchday, GF/GA running totals, GD curve, home/away split breakdowns.

### 9.2 Form & streaks
Primary source: `teamform` / `teamlongform` / `teamshortform` / `lastgameresult` / `unbeaten*` from SEASON_OVERVIEW.
Secondary source (if FIXTURES_* present): exact W/D/L history.

### 9.3 Squad performance
Inputs: PLAYERS_SNAPSHOT (form/injury/goals/appearances from `teamplayerlinks`) + SEASON_STATS.
Outputs: top scorers (verified via `istopscorer`), assists, appearances, avg rating, clean sheets (GKs), injury flags, yellow/red discipline.

### 9.4 Player development trend
Requires ≥2 PLAYERS_SNAPSHOTs from different dates.
Outputs: OVR/potential delta per player; attribute-group deltas.

### 9.5 Wonderkids
Filter: `age <= 21 AND potential >= threshold`.
Outputs: ranked list with origin badge (real vs generated via `playerid` threshold), quadrant scatter (age × potential).

### 9.6 Tactical stats
Inputs: SEASON_OVERVIEW (`buildupplay`, `defensivedepth`, team ratings), STANDINGS_* (home/away splits).
Outputs:
- goals per match (home vs away),
- goals conceded per match (home vs away),
- clean-sheet ratio (needs SEASON_STATS cross-reference for GK),
- "buildup style" and "defensive line" readouts directly from the team row.
Formation visual remains gated on §16.3 resolution.

### 9.7 Transfer planning
Inputs: PLAYERS_SNAPSHOT (+ TRANSFER_HISTORY optional).
Outputs: age × OVR quadrant, expiring contracts (`contractvaliduntil` vs current season year), positional depth chart, replacement finder.

---

## 10. Chart & Visualization Modules

All charts wrap **PyQtGraph** behind `ChartPanel(title, subtitle, x_axis, y_axis, series[])`.

| Module | Chart type | Used on |
|--------|-----------|---------|
| `line_chart` | Line + area | Points / ranking / form curve |
| `bar_chart` | Bars H/V | Top scorers, assists, appearances |
| `stacked_bar` | Stacked | W/D/L per month, home vs away GF/GA |
| `radar_chart` | Radar | Player attribute profile (6 groups) |
| `sparkline` | Inline mini | KPI tiles, table cells |
| `heatmap` | Grid | Tactical / depth views |
| `scatter` | Scatter | Age × potential / age × OVR |

Theming from a single palette (`ui/theme.py`).

---

## 11. Wonderkid Scouting Module

See §9.5 for logic and §7.4 for CSV contract.

- Sortable/filterable table (age, potential, position, league, nationality, real vs generated).
- Quadrant scatter: age × potential colored by position group (derived from `preferredposition1`).
- Per-player drawer: radar (pacdiv/shohan/paskic/driref/defspe/phypos once resolved; raw attribute list otherwise) + full attribute list.
- Origin badge: `real` vs `generated` via `playerid >= 460000`.

---

## 12. UI / Page Architecture

### 12.1 Shell

`QMainWindow` with:
- **Left sidebar** — Overview, Analytics, Squad, Wonderkids, Tactics, Transfers, Import.
- **Top bar** — season, club, global filter, import, theme toggle.
- **Central stack** — one page per section.
- **Status bar** — last import timestamp, row counts, log indicator.

### 12.2 Pages

**Season Overview** — hero header, KPI grid (Points / W / D / L / GF / GA / GD / Recent Form / Objective progress via `hasachievedobjective` + `actualvsexpectations`), sparkline per KPI.

**Season Analytics** — points progression, ranking evolution (inverted Y), scoring trend, defensive trend, form curve, streaks panel (`unbeaten*`).

**Squad Performance** — Top-N leaderboards (scorers/assists/apps/ratings/clean sheets); filter bar (competition/position/min minutes); per-player drawer with development trend (if multi-snapshot), radar, match log; inline `form` + `injury` badges.

**Wonderkid Scout Hub** — §11.

**Tactical Dashboard** — team ratings bars (overall/attack/midfield/defense, plus matchday variants); `buildupplay` / `defensivedepth` gauges; home vs away finishing/defensive efficiency. Formation pitch deferred (§16.3).

**Transfer Planning** — aging quadrant, expiring contracts table (years-left from `contractvaliduntil`), replacement finder, depth bar chart, incoming transfers counter from `teams.numtransfersin`.

**Import Page** — drag/drop zone, detected files list, parse log, clear-cache.

### 12.3 Design tokens

- **Typography**: Inter or system default, 4 sizes.
- **Spacing**: 4/8/12/16/24/32 px scale.
- **Radii**: 6 / 10 / 14 px.
- **Palette**: dark theme default, light toggle. Semantic tokens only.

---

## 13. Export-Script Workflow (Lua side)

### 13.1 Guiding rule
Only use methods already confirmed. Anything else goes to `lua_probes/` and is pcall-guarded.

### 13.2 Confirmed Live Editor API (inherited; unchanged)

#### Table access
- `LE.db:GetTable("players")`, `"teamplayerlinks"`, `"teams"`, `"leagues"`, `"leagueteamlinks"`, `"career_playercontract"`, **`"playernames"`** (newly-documented, SBDD-confirmed).

#### Record iteration
- `table:GetFirstRecord()`, `table:GetNextValidRecord()`, `table:GetRecordFieldValue(record, "field")`, `table:SetRecordFieldValue(record, "field", value)`.

#### Helpers (from prior confirmations)
- `GetPlayerName(playerid)` — slow.
- `GetTeamName(teamid)`, `GetTeamIdFromPlayerId(playerid)`, `GetPlayerIDSForTeam(teamid)`.
- `GetUserSeniorTeamPlayerIDs()`, `GetUserTeamID()`.
- `GetCurrentDate()` → `{day, month, year}`, `:ToInt()`.
- `GetPlayerPrimaryPositionName(code)`.
- `GetCompetitionNameByObjID(id)`.
- `GetPlayersStats()`.
- `GetCMEventNameByID(id)`, `AddEventHandler("pre__CareerModeEvent", cb)`, `IsInCM()`.
- `PlayerHasDevelopementPlan(playerid)`, `PlayerSetValueInDevelopementPlan(...)`.
- `MessageBox`, `Log`, `LOGGER:LogInfo`, `LOGGER:LogError`.

#### DATE class
`DATE:new()`, `:FromGregorianDays(days)`, `:ToGregorianDays()`, `:FromInt()`, `:ToInt()`, `:ToString()`; fields `.year / .month / .day`.

#### Memory helpers (advanced, reference-only)
`MEMORY:ReadPointer / ReadInt / ReadShort / ReadChar / ReadBool / ReadMultilevelPointer`.

#### Constants (confirmed)
- `playerid >= 460000` = generated, `< 460000` = real.
- Contract statuses `1 / 3 / 5` → loaned-in.

### 13.3 CSV writing pattern
```lua
local desktop_path = string.format("%s\\Desktop", os.getenv('USERPROFILE'))
local d = GetCurrentDate()
local path = string.format("%s\\<KIND>_%02d_%02d_%04d.csv", desktop_path, d.day, d.month, d.year)
local f = io.open(path, "w+")
io.output(f)
io.write(table.concat(columns, ",")); io.write("\n")
-- ... rows
io.close(f)
```

### 13.4 New production scripts
- `export_season_overview.lua` — §7.1.
- `export_standings.lua` — §7.2, one file per league the user cares about.
- `export_players_snapshot.lua` — §7.3.
- `export_wonderkids.lua` — §7.4.

Every script:
1. `assert(IsInCM())`.
2. Build a cache of `playernames` (single full scan → Lua table keyed by `nameid`) before the main loop.
3. Single pass over `players`, lazy name resolution via the cache (no `GetPlayerName` calls).
4. `pcall` any field flagged in §16.
5. Escape CSV commas/quotes in string columns.

---

## 14. Scalability, Error Handling, Extensibility

### 14.1 Scalability
- `players` ≈ tens of thousands of rows: single Lua pass; pandas handles rest.
- Each imported CSV stored in session cache keyed by `(kind, export_date)` → multi-snapshot comparisons trivial.
- Downsample in the analytics layer when a chart exceeds 5k visible points.
- Parser interface is chunkable → migrate to polars only if a CSV exceeds ~200 MB.

### 14.2 Error handling
- Typed exceptions: `MissingColumnError`, `SchemaMismatchError`, `EmptyFileError`.
- UI: `QErrorMessage` for fatal, toasts for recoverable.
- Rotating file log at `%LOCALAPPDATA%\FC26Analytics\logs\app.log`.
- Never crash silently.

### 14.3 Extensibility
- Analytics modules register via a small registry.
- New CSV kind = 1 schema entry + 1 parser + optional page.
- i18n via `tr()` from day one.
- Palette tokenized for theme packs.

---

## 15. Points to Verify — Remaining Uncertainties

SBDD eliminated most prior unknowns. The remaining items:

### 15.1 Player string-name fields
**Resolved by SBDD**: `players` holds `firstnameid` / `lastnameid` / `commonnameid` / `playerjerseynameid`; strings live in `playernames.name`. Resolution strategy: build a Lua-side `nameid → name` cache, then join.
**Unverified**: whether `playernames` contains entries for every ID used by `players` (i.e. no dangling FKs). → Probe: `probe_names_integrity.lua` dumps counts of unresolved IDs.

### 15.2 Face-aggregate attributes
SBDD lists `pacdiv`, `shohan`, `paskic`, `driref`, `defspe`, `phypos` on `players`. Naming strongly suggests the 6 front-face stats (PAC/SHO/PAS/DRI/DEF/PHY) **but encoding is unverified** (integer? packed?).
**Action**: `probe_face_aggregates.lua` — dump these 6 fields for 20 known players and compare to the in-game card.

### 15.3 Per-player form / injury semantics
`teamplayerlinks.form` and `teamplayerlinks.injury` confirmed **present**, but the value encoding is unverified (scale? enum?).
**Action**: `probe_form_injury.lua` — dump distribution and sample known-injured players.

### 15.4 Team tactics / formation
`teams.favoriteteamsheetid` is a pointer. The target table is **not** in SBDD.
**Action**: `probe_team_tactics.lua` — try `LE.db:GetTable("teamsheets")`, `"formations"`, `"teamformations"` with `pcall`.

### 15.5 Objectives semantics
Fields exist in `leagueteamlinks`. Numeric semantics of `objective` / `actualvsexpectations` / `highestprobable` unverified.
**Action**: `probe_objectives.lua` — dump user team's row + 3 rival teams' rows; compare to known in-game objective.

### 15.6 `compobjid` vs `leagueid`
`GetPlayersStats()` returns `compobjid`; `leagues.leagueid` exists. Mapping unverified.
**Action**: `probe_compobjid_mapping.lua` — cross-reference the user's domestic league.

### 15.7 Contract / wage
`career_playercontract` has no salary field in any confirmed artefact. Salary / release-clause data source unknown.
**Action**: deferred — flagged as "not v1" unless the user produces the schema.

### 15.8 Fixtures outside memory
No DB table for fixtures is confirmed. Fixtures will continue to be exported via `MEMORY:*` as in `export_fixtures.lua`.

### 15.9 Regen sub-type tagging
No field distinguishes youth-academy / regen / free-agent origin. Stay with the `>= 460000` boolean.

### 15.10 Python-side decisions
- Packaging → **locked to PyInstaller**.
- Charting fallback → PyQtGraph only; QtCharts considered only if a specific chart type is impossible.
- Cache scope → **one SQLite file per career save**, name derived from user's club + save timestamp.

---

## 16. Review Checklist Before Starting Development

- [ ] §15 probes executed; any blocker resolved.
- [ ] CSV contracts in `docs/CSV_CONTRACTS.md` finalized (one file per §7 entry).
- [ ] Sprint 0 layout reviewed (see ROADMAP.md).
- [ ] Decision on dark-only vs light+dark at v1.
- [ ] Sign-off on page list (§12.2).

---

*End of plan.*
