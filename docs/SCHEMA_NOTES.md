# Schema Notes

Status of each PT §15 "Point to Verify" after running the Sprint 1 probes.
Evidence rows are verbatim extracts from the matching `data/samples/probe_results/PROBE_*.csv`.

Legend:
- **RESOLVED** — encoding / presence confirmed by probe output.
- **PARTIAL** — probe returned some signal but not enough to freeze a contract.
- **STILL UNKNOWN** — probe did not return usable signal; downstream code must gate on presence.
- **BLOCKER** — a decision or follow-up probe is required before relying on this data.

---

## §15.1 Player string-name fields — BLOCKER

**Probe**: `probe_names_integrity.lua` → `PROBE_names_integrity_19_08_2025.csv`.

**Evidence**:
```
playernames_cache,OK,rows_cached=1,
sample_size,OK,players_sampled=200,
firstnameid_resolution,UNRESOLVED,unresolved=200;zero_values=0,pid=19541;firstnameid=13398
lastnameid_resolution,UNRESOLVED,unresolved=200;zero_values=0,pid=19541;lastnameid=25779
commonnameid_resolution,UNRESOLVED,unresolved=17;zero_values=183,pid=20801;commonnameid=7926
playerjerseynameid_resolution,UNRESOLVED,unresolved=200;zero_values=0,pid=19541;playerjerseynameid=25779
```

**Interpretation**: iterating the `playernames` table via `GetFirstRecord()` / `GetNextValidRecord()` only yielded **1 row**. All 4 nameid FKs are therefore UNRESOLVED across the 200-player sample. The 183 `zero_values` on `commonnameid` is expected (most players have no common name), but the `firstnameid` / `lastnameid` / `playerjerseynameid` integers are real and should map.

**Impact**: PT §7.3 `PLAYERS_SNAPSHOT` requires resolved `firstname`, `lastname`, `commonname`, `display_name`, `jerseyname` columns. With the current iteration pattern, the Lua-side cache approach described in PT §4.2 / §13.4 **does not work**.

**Options** (must be chosen before Sprint 2):
1. Fall back to `GetPlayerName(playerid)` per-player in the export script. Known slow — PT §13.2 flags it — but it is the only currently-confirmed alternative.
2. Investigate whether `playernames` supports a different iteration primitive (e.g. indexed access). This requires a new follow-up probe and is not in the scope of Sprint 1.

**Awaiting user direction** on which option to commit to.

---

## §15.2 Face-aggregate attributes — RESOLVED

**Probe**: `probe_face_aggregates.lua` → `PROBE_face_aggregates_19_08_2025.csv`.

**Evidence (selected)**:
```
face_aggregates,OK,compare to in-game card,playerid=231747;pacdiv=96;shohan=91;paskic=81;driref=92;defspe=37;phypos=76   # Mbappé
face_aggregates,OK,compare to in-game card,playerid=239985;pacdiv=…                                                    # Haaland (missing from output — see below)
face_aggregates,OK,compare to in-game card,playerid=243715;pacdiv=77;shohan=39;paskic=68;driref=73;defspe=88;phypos=83   # Saliba
face_aggregates,OK,compare to in-game card,playerid=256196;pacdiv=80;shohan=34;paskic=63;driref=62;defspe=87;phypos=86   # Pacho
summary,OK,found=16/17,
```

**Interpretation**: each of `pacdiv, shohan, paskic, driref, defspe, phypos` returns a direct 0–99 integer matching the six front-card stats (PAC / SHO / PAS / DRI / DEF / PHY). Defender profiles (Saliba, Pacho) correctly show low SHO and high DEF/PHY; attackers show the inverse.

**Impact**: these six fields can be consumed verbatim as PAC/SHO/PAS/DRI/DEF/PHY. No decoding needed.

**Caveats**:
- `playerid=239985` (Haaland) was not found in the sample — 16 / 17 resolved. Likely absent from this specific save's `players` table.
- We only validated directional plausibility (defender vs attacker), not exact equality with the card. If a later mismatch appears, re-check on a larger sample.

---

## §15.3 Per-player form / injury — PARTIAL (awaiting re-run)

**Probe**: `probe_form_injury.lua` → `PROBE_form_injury_19_08_2025.csv`.

**Evidence**:
```
total_rows,OK,rows=21848,
form_errors,OK,read_errors=0,
injury_errors,OK,read_errors=0,
```

**Interpretation**: `teamplayerlinks.form` and `teamplayerlinks.injury` exist and read without error on all 21,848 rows. The histogram rows were **not written** because the probe's sort comparator had an operator-precedence bug that aborted execution after the successful-read totals but before histogram emission.

**Status**: bug fixed in `lua_probes/probe_form_injury.lua` (parenthesized `(tonumber(a) or 0) < (tonumber(b) or 0)`). Awaiting user re-run to capture the value distribution and freeze the encoding.

**Impact**: fields are confirmed present and readable. The analytics in PT §9.3 (`injury_list`, `form_leaders`) can be wired in Sprint 7, but thresholds for "is injured" / "good form" cannot be fixed until the histogram lands.

---

## §15.4 Team tactics / formation — PARTIAL

**Probe**: `probe_team_tactics.lua` → `PROBE_team_tactics_19_08_2025.csv`.

**Evidence**:
```
teams.favoriteteamsheetid,OK,read from first teams record,value=-1
table:teamsheets,OK,opened; probing candidate columns,
table:teamsheets:columns,OK,columns confirmed on first record,teamsheetid=0;teamid=0
table:formations,OK,opened; probing candidate columns,
table:formations:columns,OK,columns confirmed on first record,formationid=1;formationname=4-1-3-2;teamid=-1;position1=3;position2=4;position3=6;position4=7;position5=10;position6=12;position7=14;position8=16;position9=24;position10=26
table:teamformations,MISSING,LE.db:GetTable failed,
table:team_tactics,MISSING,LE.db:GetTable failed,
```

**Interpretation**:
- `formations` is a real table. Each row has `formationid`, `formationname` (e.g. `"4-1-3-2"`), `teamid`, and numeric position-code columns `position1..position10`. `position11` was not reported on the first record — it may be missing, or it held a value the probe skipped; this is minor.
- `teamsheets` exists but the first row is a placeholder (`teamsheetid=0, teamid=0`); a richer scan would be needed to confirm its columns.
- `teamformations` and `team_tactics` are not accessible via `LE.db:GetTable`.
- `teams.favoriteteamsheetid=-1` on the first team (likely a default/empty record). Whether the **user's** team has a real pointer remains unprobed.

**Impact**: a basic formation render (name + 10 position codes) is feasible from `formations` alone. A per-team tactical view via `teamsheets`/`favoriteteamsheetid` requires another follow-up probe before the Sprint 11 formation-pitch visual can ship. The Sprint 11 fallback "Formation data unavailable" placeholder remains valid.

---

## §15.5 Objectives semantics — STILL UNKNOWN

**Probe**: `probe_objectives.lua` → `PROBE_objectives_19_08_2025.csv`.

**Evidence**:
```
user_team,OK,GetUserTeamID(),teamid=243
rivals,OK,rivals_found=2,ids=241;240
user_objectives,OK,from leagueteamlinks,teamid=243;leagueid=53;objective=0;hasachievedobjective=0;highestpossible=0;highestprobable=1;yettowin=0;actualvsexpectations=0;champion=0
rival_objectives,OK,from leagueteamlinks,teamid=240;leagueid=53;objective=0;hasachievedobjective=0;highestpossible=0;highestprobable=1;yettowin=0;actualvsexpectations=0;champion=0
rival_objectives,OK,from leagueteamlinks,teamid=241;leagueid=53;objective=0;hasachievedobjective=0;highestpossible=0;highestprobable=0;yettowin=0;actualvsexpectations=0;champion=1
```

**Interpretation**: all objective fields are present and readable, but at the current moment in the career save they are mostly zero. Only `champion=1` fires for one rival (teamid 241 — marked "reigning champion"). `highestpossible=0, highestprobable ∈ {0,1}` suggests these are either pre-season placeholders or flags rather than ordinal rankings.

**Impact**: the fields can be exported (PT §7.1 SEASON_OVERVIEW includes them) but the UI must treat them as opaque integers until a mid-season probe clarifies semantics.

**Follow-up** (deferred): re-run this probe after ≥10 matchdays to observe non-zero values.

---

## §15.6 `compobjid` vs `leagueid` — STILL UNKNOWN (direct)

**Probe**: `probe_compobjid_mapping.lua` → `PROBE_compobjid_mapping_19_08_2025.csv`.

**Evidence (excerpt)**:
```
comp_entry,OK,compobjid=1391,compname=LALIGA EA SPORTS
comp_entry,OK,compobjid=777, compname=Premier League
comp_entry,OK,compobjid=875, compname=Ligue 1 McDonald's
league_entry,OK,leagueid=13,leaguename=England Premier League (1);level=1
league_entry,OK,leagueid=16,leaguename=France Ligue 1 (1);level=1
league_entry,OK,leagueid=53,leaguename=Spain Primera División (1);level=1
```

**Interpretation**: there is **no direct integer mapping** — e.g. Primera División is `leagueid=53` but `compobjid=1391`. The two tables use independent ID spaces.

**Impact**: linking `SEASON_STATS` (carries `compobjid`) to `STANDINGS` / `SEASON_OVERVIEW` (carries `leagueid`) requires an explicit lookup table keyed by `compname` ↔ `leaguename`, built either statically in Python or via a one-time calibration probe. Fuzzy matching will be needed because names don't align literally (`"LALIGA EA SPORTS"` vs `"Spain Primera División (1)"`).

**Plan**: freeze a manual mapping in `app/core/constants.py` during Sprint 4, derived from this CSV.

---

## §15.7 Contract / wage — DEFERRED

No probe written. PT §15.7 explicitly defers this to post-v1. No salary / release-clause field is currently confirmed on any table.

---

## §15.8 Fixtures outside memory — PRE-RESOLVED

No DB table confirmed. Fixtures continue to be exported via `MEMORY:*` helpers as in `lua_exports/export_fixtures.lua`. Nothing to probe.

---

## §15.9 Regen sub-type tagging — PRE-RESOLVED

No dedicated field. Stay with the PT-defined boolean `is_generated = (playerid >= 460000)`.

---

## §15.10 Python-side decisions — PRE-RESOLVED

Locked in PT §15.10 (PyInstaller packaging, PyQtGraph-only charting, one SQLite per career save). No probe needed.

---

## Summary table

| § | Topic | Status | Blocker? |
|---|---|---|---|
| 15.1 | Player names via `playernames` | BLOCKER | ✅ — see "Options" above |
| 15.2 | Face aggregates (PAC/SHO/…) | RESOLVED | — |
| 15.3 | `teamplayerlinks.form` / `.injury` | PARTIAL (re-run pending) | — |
| 15.4 | Formations / teamsheets | PARTIAL | — (Sprint 11 placeholder OK) |
| 15.5 | Objective fields semantics | STILL UNKNOWN | — |
| 15.6 | `compobjid` ↔ `leagueid` | STILL UNKNOWN (direct) | name-based map needed |
| 15.7 | Contract / wage | DEFERRED | — |
| 15.8 | Fixtures | PRE-RESOLVED | — |
| 15.9 | Regen tagging | PRE-RESOLVED | — |
| 15.10 | Python-side decisions | PRE-RESOLVED | — |
