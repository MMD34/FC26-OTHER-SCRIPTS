# CSV Contracts

Frozen column contracts for every CSV kind consumed by the Python import pipeline.
Source of truth: **PLAN_TECHNIQUE.md §7**. No column exists here that is not in PT §7.

Column metadata:
- `name` — column header as written by the Lua export script.
- `dtype` — pandas dtype used by the parser (Sprint 4).
- `nullable` — whether the parser tolerates missing values.
- `source` — `<sbdd_table>.<sbdd_column>` (or "computed" / "memory" / "GetPlayersStats").
- `notes` — constraints, encodings, cross-refs to `SCHEMA_NOTES.md`.

Shared header on every CSV: `export_date` = `DD_MM_YYYY` from `GetCurrentDate()`.

---

## 7.1 `SEASON_OVERVIEW_DD_MM_YYYY.csv`

One row per `(user team × current league)`.

Source: `leagueteamlinks` (filtered to user team) + `leagues` + `teams`.

| name | dtype | nullable | source | notes |
|---|---|---|---|---|
| export_date | string | no | computed | `DD_MM_YYYY` |
| season_year | Int64 | no | `GetCurrentDate().year` | computed in Lua |
| user_teamid | Int64 | no | `GetUserTeamID()` | |
| user_teamname | string | no | `teams.teamname` | |
| leagueid | Int64 | no | `leagueteamlinks.leagueid` | |
| leaguename | string | no | `leagues.leaguename` | |
| league_level | Int64 | yes | `leagues.level` | |
| leaguetype | Int64 | yes | `leagues.leaguetype` | |
| currenttableposition | Int64 | no | `leagueteamlinks.currenttableposition` | |
| previousyeartableposition | Int64 | yes | `leagueteamlinks.previousyeartableposition` | |
| points | Int64 | no | `leagueteamlinks.points` | |
| nummatchesplayed | Int64 | no | `leagueteamlinks.nummatchesplayed` | |
| homewins | Int64 | no | `leagueteamlinks.homewins` | |
| homedraws | Int64 | no | `leagueteamlinks.homedraws` | |
| homelosses | Int64 | no | `leagueteamlinks.homelosses` | |
| awaywins | Int64 | no | `leagueteamlinks.awaywins` | |
| awaydraws | Int64 | no | `leagueteamlinks.awaydraws` | |
| awaylosses | Int64 | no | `leagueteamlinks.awaylosses` | |
| homegf | Int64 | no | `leagueteamlinks.homegf` | |
| homega | Int64 | no | `leagueteamlinks.homega` | |
| awaygf | Int64 | no | `leagueteamlinks.awaygf` | |
| awayga | Int64 | no | `leagueteamlinks.awayga` | |
| teamform | string | yes | `leagueteamlinks.teamform` | encoding TBD |
| teamshortform | string | yes | `leagueteamlinks.teamshortform` | encoding TBD |
| teamlongform | string | yes | `leagueteamlinks.teamlongform` | encoding TBD |
| lastgameresult | Int64 | yes | `leagueteamlinks.lastgameresult` | |
| unbeatenhome | Int64 | yes | `leagueteamlinks.unbeatenhome` | |
| unbeatenaway | Int64 | yes | `leagueteamlinks.unbeatenaway` | |
| unbeatenleague | Int64 | yes | `leagueteamlinks.unbeatenleague` | |
| unbeatenallcomps | Int64 | yes | `leagueteamlinks.unbeatenallcomps` | |
| objective | Int64 | yes | `leagueteamlinks.objective` | semantics TBD — §15.5 |
| hasachievedobjective | boolean | yes | `leagueteamlinks.hasachievedobjective` | |
| highestpossible | Int64 | yes | `leagueteamlinks.highestpossible` | §15.5 |
| highestprobable | Int64 | yes | `leagueteamlinks.highestprobable` | §15.5 |
| yettowin | Int64 | yes | `leagueteamlinks.yettowin` | §15.5 |
| actualvsexpectations | Int64 | yes | `leagueteamlinks.actualvsexpectations` | §15.5 |
| champion | boolean | yes | `leagueteamlinks.champion` | |
| team_overallrating | Int64 | no | `teams.overallrating` | |
| team_attackrating | Int64 | no | `teams.attackrating` | |
| team_midfieldrating | Int64 | no | `teams.midfieldrating` | |
| team_defenserating | Int64 | no | `teams.defenserating` | |
| buildupplay | Int64 | yes | `teams.buildupplay` | |
| defensivedepth | Int64 | yes | `teams.defensivedepth` | |
| captainid | Int64 | yes | `teams.captainid` | |
| penaltytakerid | Int64 | yes | `teams.penaltytakerid` | |
| freekicktakerid | Int64 | yes | `teams.freekicktakerid` | |
| leftcornerkicktakerid | Int64 | yes | `teams.leftcornerkicktakerid` | |
| rightcornerkicktakerid | Int64 | yes | `teams.rightcornerkicktakerid` | |
| longkicktakerid | Int64 | yes | `teams.longkicktakerid` | |
| leftfreekicktakerid | Int64 | yes | `teams.leftfreekicktakerid` | |
| rightfreekicktakerid | Int64 | yes | `teams.rightfreekicktakerid` | |
| favoriteteamsheetid | Int64 | yes | `teams.favoriteteamsheetid` | `-1` = unset per probe |
| teamstadiumcapacity | Int64 | yes | `teams.teamstadiumcapacity` | |
| clubworth | Int64 | yes | `teams.clubworth` | |
| domesticprestige | Int64 | yes | `teams.domesticprestige` | |
| internationalprestige | Int64 | yes | `teams.internationalprestige` | |

Required columns: `export_date, season_year, user_teamid, leagueid, points, nummatchesplayed, currenttableposition`.

---

## 7.2 `STANDINGS_<league>_DD_MM_YYYY.csv`

One row per team in `leagueid = <league>`. Filename: league name sanitized (non-`[A-Za-z0-9_-]` → `_`).

Source: `leagueteamlinks WHERE leagueid = <league>` JOIN `teams`.

| name | dtype | nullable | source | notes |
|---|---|---|---|---|
| export_date | string | no | computed | |
| leagueid | Int64 | no | `leagueteamlinks.leagueid` | |
| leaguename | string | no | `leagues.leaguename` | |
| teamid | Int64 | no | `leagueteamlinks.teamid` | |
| teamname | string | no | `teams.teamname` | |
| currenttableposition | Int64 | no | `leagueteamlinks.currenttableposition` | |
| previousyeartableposition | Int64 | yes | `leagueteamlinks.previousyeartableposition` | |
| points | Int64 | no | `leagueteamlinks.points` | |
| nummatchesplayed | Int64 | no | `leagueteamlinks.nummatchesplayed` | |
| homewins | Int64 | no | `leagueteamlinks.homewins` | |
| homedraws | Int64 | no | `leagueteamlinks.homedraws` | |
| homelosses | Int64 | no | `leagueteamlinks.homelosses` | |
| awaywins | Int64 | no | `leagueteamlinks.awaywins` | |
| awaydraws | Int64 | no | `leagueteamlinks.awaydraws` | |
| awaylosses | Int64 | no | `leagueteamlinks.awaylosses` | |
| homegf | Int64 | no | `leagueteamlinks.homegf` | |
| homega | Int64 | no | `leagueteamlinks.homega` | |
| awaygf | Int64 | no | `leagueteamlinks.awaygf` | |
| awayga | Int64 | no | `leagueteamlinks.awayga` | |
| teamform | string | yes | `leagueteamlinks.teamform` | |
| teamlongform | string | yes | `leagueteamlinks.teamlongform` | |
| lastgameresult | Int64 | yes | `leagueteamlinks.lastgameresult` | |
| unbeatenleague | Int64 | yes | `leagueteamlinks.unbeatenleague` | |
| champion | boolean | yes | `leagueteamlinks.champion` | |
| team_overallrating | Int64 | no | `teams.overallrating` | |

Required columns: `export_date, leagueid, teamid, points, nummatchesplayed, currenttableposition`.

---

## 7.3 `PLAYERS_SNAPSHOT_DD_MM_YYYY.csv`

One row per player. Source: `players` JOIN `teamplayerlinks` on `playerid`, JOIN `teams` on `teamid`, JOIN `leagueteamlinks` on `teamid` for `leagueid`, JOIN `playernames` ×4 for names.

| name | dtype | nullable | source | notes |
|---|---|---|---|---|
| export_date | string | no | computed | |
| playerid | Int64 | no | `players.playerid` | |
| is_generated | boolean | no | computed | `playerid >= 460000` |
| firstname | string | yes | `playernames.name` via `firstnameid` | §15.1 blocker |
| lastname | string | yes | `playernames.name` via `lastnameid` | §15.1 blocker |
| commonname | string | yes | `playernames.name` via `commonnameid` | §15.1 blocker |
| display_name | string | yes | computed in Lua | commonname → first+last → jersey |
| jerseyname | string | yes | `playernames.name` via `playerjerseynameid` | §15.1 blocker |
| birthdate | Int64 | no | `players.birthdate` | Gregorian-day |
| age | Int64 | no | computed in Lua | from birthdate + `GetCurrentDate()` |
| nationality | Int64 | yes | `players.nationality` | |
| gender | Int64 | yes | `players.gender` | |
| preferredfoot | Int64 | yes | `players.preferredfoot` | |
| preferredposition1 | Int64 | no | `players.preferredposition1` | |
| preferredposition2 | Int64 | yes | `players.preferredposition2` | |
| preferredposition3 | Int64 | yes | `players.preferredposition3` | |
| preferredposition4 | Int64 | yes | `players.preferredposition4` | |
| preferredposition5 | Int64 | yes | `players.preferredposition5` | |
| preferredposition6 | Int64 | yes | `players.preferredposition6` | |
| preferredposition7 | Int64 | yes | `players.preferredposition7` | |
| role1 | Int64 | yes | `players.role1` | |
| role2 | Int64 | yes | `players.role2` | |
| role3 | Int64 | yes | `players.role3` | |
| role4 | Int64 | yes | `players.role4` | |
| role5 | Int64 | yes | `players.role5` | |
| overallrating | Int64 | no | `players.overallrating` | |
| potential | Int64 | no | `players.potential` | |
| internationalrep | Int64 | yes | `players.internationalrep` | |
| pacdiv | Int64 | yes | `players.pacdiv` | PAC (0–99) — §15.2 resolved |
| shohan | Int64 | yes | `players.shohan` | SHO (0–99) |
| paskic | Int64 | yes | `players.paskic` | PAS (0–99) |
| driref | Int64 | yes | `players.driref` | DRI (0–99) |
| defspe | Int64 | yes | `players.defspe` | DEF (0–99) |
| phypos | Int64 | yes | `players.phypos` | PHY (0–99) |
| gkdiving | Int64 | yes | `players.gkdiving` | |
| gkhandling | Int64 | yes | `players.gkhandling` | |
| gkkicking | Int64 | yes | `players.gkkicking` | |
| gkpositioning | Int64 | yes | `players.gkpositioning` | |
| gkreflexes | Int64 | yes | `players.gkreflexes` | |
| crossing | Int64 | yes | `players.crossing` | |
| finishing | Int64 | yes | `players.finishing` | |
| headingaccuracy | Int64 | yes | `players.headingaccuracy` | |
| shortpassing | Int64 | yes | `players.shortpassing` | |
| volleys | Int64 | yes | `players.volleys` | |
| defensiveawareness | Int64 | yes | `players.defensiveawareness` | |
| standingtackle | Int64 | yes | `players.standingtackle` | |
| slidingtackle | Int64 | yes | `players.slidingtackle` | |
| dribbling | Int64 | yes | `players.dribbling` | |
| curve | Int64 | yes | `players.curve` | |
| freekickaccuracy | Int64 | yes | `players.freekickaccuracy` | |
| longpassing | Int64 | yes | `players.longpassing` | |
| ballcontrol | Int64 | yes | `players.ballcontrol` | |
| shotpower | Int64 | yes | `players.shotpower` | |
| jumping | Int64 | yes | `players.jumping` | |
| stamina | Int64 | yes | `players.stamina` | |
| strength | Int64 | yes | `players.strength` | |
| longshots | Int64 | yes | `players.longshots` | |
| acceleration | Int64 | yes | `players.acceleration` | |
| sprintspeed | Int64 | yes | `players.sprintspeed` | |
| agility | Int64 | yes | `players.agility` | |
| reactions | Int64 | yes | `players.reactions` | |
| balance | Int64 | yes | `players.balance` | |
| aggression | Int64 | yes | `players.aggression` | |
| composure | Int64 | yes | `players.composure` | |
| interceptions | Int64 | yes | `players.interceptions` | |
| positioning | Int64 | yes | `players.positioning` | |
| vision | Int64 | yes | `players.vision` | |
| penalties | Int64 | yes | `players.penalties` | |
| trait1 | Int64 | yes | `players.trait1` | |
| trait2 | Int64 | yes | `players.trait2` | |
| icontrait1 | Int64 | yes | `players.icontrait1` | |
| icontrait2 | Int64 | yes | `players.icontrait2` | |
| skillmoves | Int64 | yes | `players.skillmoves` | |
| skillmoveslikelihood | Int64 | yes | `players.skillmoveslikelihood` | |
| weakfootabilitytypecode | Int64 | yes | `players.weakfootabilitytypecode` | |
| height | Int64 | yes | `players.height` | |
| weight | Int64 | yes | `players.weight` | |
| contractvaliduntil | Int64 | yes | `players.contractvaliduntil` | |
| playerjointeamdate | Int64 | yes | `players.playerjointeamdate` | Gregorian-day |
| isretiring | boolean | yes | `players.isretiring` | |
| teamid | Int64 | yes | `teamplayerlinks.teamid` | |
| teamname | string | yes | `teams.teamname` | |
| jerseynumber | Int64 | yes | `teamplayerlinks.jerseynumber` | |
| squad_position | Int64 | yes | `teamplayerlinks.position` | |
| leagueid | Int64 | yes | `leagueteamlinks.leagueid` | |
| leaguename | string | yes | `leagues.leaguename` | |
| league_level | Int64 | yes | `leagues.level` | |
| form | Int64 | yes | `teamplayerlinks.form` | encoding TBD — §15.3 |
| injury | Int64 | yes | `teamplayerlinks.injury` | encoding TBD — §15.3 |
| leagueappearances | Int64 | yes | `teamplayerlinks.leagueappearances` | |
| leaguegoals | Int64 | yes | `teamplayerlinks.leaguegoals` | |
| leaguegoalsprevmatch | Int64 | yes | `teamplayerlinks.leaguegoalsprevmatch` | |
| leaguegoalsprevthreematches | Int64 | yes | `teamplayerlinks.leaguegoalsprevthreematches` | |
| yellows | Int64 | yes | `teamplayerlinks.yellows` | |
| reds | Int64 | yes | `teamplayerlinks.reds` | |
| istopscorer | boolean | yes | `teamplayerlinks.istopscorer` | |
| isamongtopscorers | boolean | yes | `teamplayerlinks.isamongtopscorers` | |
| isamongtopscorersinteam | boolean | yes | `teamplayerlinks.isamongtopscorersinteam` | |

Required columns: `export_date, playerid, is_generated, overallrating, potential, birthdate, age, preferredposition1`.

---

## 7.4 `WONDERKIDS_DD_MM_YYYY.csv`

Identical column set to `PLAYERS_SNAPSHOT`. Row filter applied in Lua:

```
age <= MAX_AGE AND potential >= POTENTIAL_MIN
```

Defaults: `MAX_AGE = 21`, `POTENTIAL_MIN = 85` (PT §7.4, constants at top of `export_wonderkids.lua`).

Required columns: same as §7.3.

---

## 7.5 `SEASON_STATS_DD_MM_YYYY.csv`

Unchanged from existing `lua_exports/export_season_stats.lua`. Source: `GetPlayersStats()` + `players`.

| name | dtype | nullable | source | notes |
|---|---|---|---|---|
| position | string | yes | `GetPlayerPrimaryPositionName(players.preferredposition1)` | |
| playerid | Int64 | no | `GetPlayersStats().playerid` | |
| playername | string | yes | `GetPlayerName(playerid)` | |
| team | string | yes | `GetTeamName(GetTeamIdFromPlayerId(playerid))` | |
| competition | string | yes | `GetPlayersStats().compname` | |
| appearances | Int64 | no | `GetPlayersStats().app` | `> 0` filter in Lua |
| AVG | string | yes | `GetPlayersStats().avg` (normalized) | two-decimal string |
| MOTMs | Int64 | yes | `GetPlayersStats().motm` | |
| goals | Int64 | yes | `GetPlayersStats().goals` | |
| assists | Int64 | yes | `GetPlayersStats().assists` | |
| yellow_cards | Int64 | yes | `GetPlayersStats().yellow` | |
| two_yellow | Int64 | yes | `GetPlayersStats().two_yellow` | |
| red_cards | Int64 | yes | `GetPlayersStats().red` | |
| saves | Int64 | yes | `GetPlayersStats().saves` | |
| goals_conceded | Int64 | yes | `GetPlayersStats().goals_conceded` | |
| cleansheets | Int64 | yes | `GetPlayersStats().clean_sheets` | |

Also carried for join in Sprint 4: `compobjid` (Int64). Name↔`leagueid` map (§15.6) applied in Python.

Required columns: `playerid, appearances, competition`.

---

## 7.6 `FIXTURES_<competition>_DD_MM_YYYY.csv`

Unchanged (memory-sourced). Contract frozen as produced by the existing `lua_exports/export_fixtures.lua`. The Python parser will defensively match the file's actual header against the PT §15.8 note. Any contract change must be made to that script first.

---

## 7.7 `TRANSFER_HISTORY_DD_MM_YYYY.csv`

Unchanged (memory-sourced). Contract frozen as produced by the existing `lua_exports/export_transfer_history.lua`. Same defensive-header rule as §7.6.

---

## Cross-cutting rules (applied by Sprint 4 parsers)

- IDs → `Int64` (nullable). Raw Gregorian-day fields kept as `Int64`; a sibling `<col>_dt` datetime column is added by the helper in `app/import_/parsers.py`.
- Booleans written by Lua as `0` / `1` are coerced to `boolean`.
- `nil` / empty string values are read as pandas `NA`.
- Extra columns in the CSV are tolerated. Missing **required** columns raise `MissingColumnError`.
- String fields containing `,` or `"` or newline are wrapped in `"` and internal `"` doubled on the Lua side.
