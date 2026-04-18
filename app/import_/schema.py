"""Frozen CSV schemas per kind (columns, dtypes, required).

Column lists are copied verbatim from docs/CSV_CONTRACTS.md (PT §7.1-§7.7).
No column appears here that is not in that contract.
"""
from __future__ import annotations

from app.core.constants import CSVKind

SEASON_OVERVIEW_COLUMNS: tuple[str, ...] = (
    "export_date", "season_year",
    "user_teamid", "user_teamname",
    "leagueid", "leaguename", "league_level", "leaguetype",
    "currenttableposition", "previousyeartableposition",
    "points", "nummatchesplayed",
    "homewins", "homedraws", "homelosses",
    "awaywins", "awaydraws", "awaylosses",
    "homegf", "homega", "awaygf", "awayga",
    "teamform", "teamshortform", "teamlongform", "lastgameresult",
    "unbeatenhome", "unbeatenaway", "unbeatenleague", "unbeatenallcomps",
    "objective", "hasachievedobjective", "highestpossible", "highestprobable",
    "yettowin", "actualvsexpectations", "champion",
    "team_overallrating", "team_attackrating", "team_midfieldrating", "team_defenserating",
    "buildupplay", "defensivedepth",
    "captainid", "penaltytakerid", "freekicktakerid",
    "leftcornerkicktakerid", "rightcornerkicktakerid",
    "longkicktakerid", "leftfreekicktakerid", "rightfreekicktakerid",
    "favoriteteamsheetid",
    "teamstadiumcapacity", "clubworth", "domesticprestige", "internationalprestige",
)

STANDINGS_COLUMNS: tuple[str, ...] = (
    "export_date",
    "leagueid", "leaguename",
    "teamid", "teamname",
    "currenttableposition", "previousyeartableposition",
    "points", "nummatchesplayed",
    "homewins", "homedraws", "homelosses",
    "awaywins", "awaydraws", "awaylosses",
    "homegf", "homega", "awaygf", "awayga",
    "teamform", "teamlongform", "lastgameresult",
    "unbeatenleague", "champion",
    "team_overallrating",
)

PLAYERS_SNAPSHOT_COLUMNS: tuple[str, ...] = (
    "export_date",
    "playerid", "is_generated",
    "firstname", "lastname", "commonname", "display_name", "jerseyname",
    "birthdate", "age",
    "nationality", "gender", "preferredfoot",
    "preferredposition1", "preferredposition2", "preferredposition3", "preferredposition4",
    "preferredposition5", "preferredposition6", "preferredposition7",
    "role1", "role2", "role3", "role4", "role5",
    "overallrating", "potential", "internationalrep",
    "pacdiv", "shohan", "paskic", "driref", "defspe", "phypos",
    "gkdiving", "gkhandling", "gkkicking", "gkpositioning", "gkreflexes",
    "crossing", "finishing", "headingaccuracy", "shortpassing", "volleys",
    "defensiveawareness", "standingtackle", "slidingtackle", "dribbling", "curve",
    "freekickaccuracy", "longpassing", "ballcontrol", "shotpower", "jumping",
    "stamina", "strength", "longshots", "acceleration", "sprintspeed",
    "agility", "reactions", "balance", "aggression", "composure",
    "interceptions", "positioning", "vision", "penalties",
    "trait1", "trait2", "icontrait1", "icontrait2",
    "skillmoves", "skillmoveslikelihood", "weakfootabilitytypecode",
    "height", "weight",
    "contractvaliduntil", "playerjointeamdate", "isretiring",
    "teamid", "teamname", "jerseynumber", "squad_position",
    "leagueid", "leaguename", "league_level",
    "form", "injury",
    "leagueappearances", "leaguegoals",
    "leaguegoalsprevmatch", "leaguegoalsprevthreematches",
    "yellows", "reds",
    "istopscorer", "isamongtopscorers", "isamongtopscorersinteam",
)

WONDERKIDS_COLUMNS: tuple[str, ...] = PLAYERS_SNAPSHOT_COLUMNS

SEASON_STATS_COLUMNS: tuple[str, ...] = (
    "position", "playerid", "playername", "team", "competition",
    "appearances", "AVG", "MOTMs",
    "goals", "assists",
    "yellow_cards", "two_yellow", "red_cards",
    "saves", "goals_conceded", "cleansheets",
)

FIXTURES_COLUMNS: tuple[str, ...] = (
    "competition", "compobjid",
    "hometeamid", "awayteamid",
    "hometeam", "homescore", "awayscore", "awayteam",
    "date", "time",
)

TRANSFER_HISTORY_COLUMNS: tuple[str, ...] = (
    "type", "date",
    "playerid", "exchangeplayerid",
    "teamfromid", "teamtoid",
    "playername", "exchangeplayername",
    "teamfromname", "teamtoname",
    "fee", "total_deal_value",
)

COLUMNS: dict[CSVKind, tuple[str, ...]] = {
    "season_overview": SEASON_OVERVIEW_COLUMNS,
    "standings": STANDINGS_COLUMNS,
    "players_snapshot": PLAYERS_SNAPSHOT_COLUMNS,
    "wonderkids": WONDERKIDS_COLUMNS,
    "season_stats": SEASON_STATS_COLUMNS,
    "fixtures": FIXTURES_COLUMNS,
    "transfer_history": TRANSFER_HISTORY_COLUMNS,
}


# --- dtypes ------------------------------------------------------------------

_INT_OVERVIEW = {
    "season_year", "user_teamid", "leagueid", "league_level", "leaguetype",
    "currenttableposition", "previousyeartableposition",
    "points", "nummatchesplayed",
    "homewins", "homedraws", "homelosses",
    "awaywins", "awaydraws", "awaylosses",
    "homegf", "homega", "awaygf", "awayga",
    "lastgameresult",
    "unbeatenhome", "unbeatenaway", "unbeatenleague", "unbeatenallcomps",
    "objective", "highestpossible", "highestprobable",
    "yettowin", "actualvsexpectations",
    "team_overallrating", "team_attackrating", "team_midfieldrating", "team_defenserating",
    "buildupplay", "defensivedepth",
    "captainid", "penaltytakerid", "freekicktakerid",
    "leftcornerkicktakerid", "rightcornerkicktakerid",
    "longkicktakerid", "leftfreekicktakerid", "rightfreekicktakerid",
    "favoriteteamsheetid",
    "teamstadiumcapacity", "clubworth", "domesticprestige", "internationalprestige",
}
_BOOL_OVERVIEW = {"hasachievedobjective", "champion"}
_STR_OVERVIEW = {
    "export_date", "user_teamname", "leaguename",
    "teamform", "teamshortform", "teamlongform",
}

_INT_STANDINGS = {
    "leagueid", "teamid",
    "currenttableposition", "previousyeartableposition",
    "points", "nummatchesplayed",
    "homewins", "homedraws", "homelosses",
    "awaywins", "awaydraws", "awaylosses",
    "homegf", "homega", "awaygf", "awayga",
    "lastgameresult", "unbeatenleague",
    "team_overallrating",
}
_BOOL_STANDINGS = {"champion"}
_STR_STANDINGS = {"export_date", "leaguename", "teamname", "teamform", "teamlongform"}

_STR_PLAYER = {
    "export_date",
    "firstname", "lastname", "commonname", "display_name", "jerseyname",
    "teamname", "leaguename",
}
_BOOL_PLAYER = {
    "is_generated", "isretiring",
    "istopscorer", "isamongtopscorers", "isamongtopscorersinteam",
}
_INT_PLAYER = set(PLAYERS_SNAPSHOT_COLUMNS) - _STR_PLAYER - _BOOL_PLAYER

_INT_SEASON_STATS = {
    "playerid", "appearances", "MOTMs",
    "goals", "assists",
    "yellow_cards", "two_yellow", "red_cards",
    "saves", "goals_conceded", "cleansheets",
}
_STR_SEASON_STATS = {"position", "playername", "team", "competition", "AVG"}

_INT_FIXTURES = {"compobjid", "hometeamid", "awayteamid", "homescore", "awayscore"}
_STR_FIXTURES = {"competition", "hometeam", "awayteam", "date", "time"}

_INT_TRANSFERS = {"playerid", "exchangeplayerid", "teamfromid", "teamtoid", "fee", "total_deal_value"}
_STR_TRANSFERS = {"type", "date", "playername", "exchangeplayername", "teamfromname", "teamtoname"}


def _dtypes(columns: tuple[str, ...], ints: set[str], strs: set[str], bools: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for c in columns:
        if c in ints:
            out[c] = "Int64"
        elif c in bools:
            out[c] = "boolean"
        elif c in strs:
            out[c] = "string"
        else:
            out[c] = "string"
    return out


DTYPES: dict[CSVKind, dict[str, str]] = {
    "season_overview": _dtypes(SEASON_OVERVIEW_COLUMNS, _INT_OVERVIEW, _STR_OVERVIEW, _BOOL_OVERVIEW),
    "standings": _dtypes(STANDINGS_COLUMNS, _INT_STANDINGS, _STR_STANDINGS, _BOOL_STANDINGS),
    "players_snapshot": _dtypes(PLAYERS_SNAPSHOT_COLUMNS, _INT_PLAYER, _STR_PLAYER, _BOOL_PLAYER),
    "wonderkids": _dtypes(WONDERKIDS_COLUMNS, _INT_PLAYER, _STR_PLAYER, _BOOL_PLAYER),
    "season_stats": _dtypes(SEASON_STATS_COLUMNS, _INT_SEASON_STATS, _STR_SEASON_STATS, set()),
    "fixtures": _dtypes(FIXTURES_COLUMNS, _INT_FIXTURES, _STR_FIXTURES, set()),
    "transfer_history": _dtypes(TRANSFER_HISTORY_COLUMNS, _INT_TRANSFERS, _STR_TRANSFERS, set()),
}


REQUIRED_COLUMNS: dict[CSVKind, frozenset[str]] = {
    "season_overview": frozenset({
        "export_date", "season_year", "user_teamid", "leagueid",
        "points", "nummatchesplayed", "currenttableposition",
    }),
    "standings": frozenset({
        "export_date", "leagueid", "teamid",
        "points", "nummatchesplayed", "currenttableposition",
    }),
    "players_snapshot": frozenset({
        "export_date", "playerid", "is_generated",
        "overallrating", "potential", "birthdate", "age", "preferredposition1",
    }),
    "wonderkids": frozenset({
        "export_date", "playerid", "is_generated",
        "overallrating", "potential", "birthdate", "age", "preferredposition1",
    }),
    "season_stats": frozenset({"playerid", "appearances", "competition"}),
    "fixtures": frozenset({"competition", "hometeamid", "awayteamid"}),
    "transfer_history": frozenset({"type", "playerid"}),
}

DATE_COLUMNS: dict[CSVKind, tuple[str, ...]] = {
    "season_overview": (),
    "standings": (),
    "players_snapshot": ("birthdate", "playerjointeamdate"),
    "wonderkids": ("birthdate", "playerjointeamdate"),
    "season_stats": (),
    "fixtures": (),
    "transfer_history": (),
}
