"""SeasonOverview domain object matching PT §7.1 SEASON_OVERVIEW columns."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from app.domain.player import _opt_bool, _opt_int, _opt_str


@dataclass
class SeasonOverview:
    export_date: str
    season_year: int
    user_teamid: int
    user_teamname: Optional[str]
    leagueid: int
    leaguename: Optional[str]
    league_level: Optional[int]
    leaguetype: Optional[int]
    currenttableposition: Optional[int]
    previousyeartableposition: Optional[int]
    points: int
    nummatchesplayed: int
    homewins: Optional[int]
    homedraws: Optional[int]
    homelosses: Optional[int]
    awaywins: Optional[int]
    awaydraws: Optional[int]
    awaylosses: Optional[int]
    homegf: Optional[int]
    homega: Optional[int]
    awaygf: Optional[int]
    awayga: Optional[int]
    teamform: Optional[str]
    teamshortform: Optional[str]
    teamlongform: Optional[str]
    lastgameresult: Optional[int]
    unbeatenhome: Optional[int]
    unbeatenaway: Optional[int]
    unbeatenleague: Optional[int]
    unbeatenallcomps: Optional[int]
    objective: Optional[int]
    hasachievedobjective: Optional[bool]
    highestpossible: Optional[int]
    highestprobable: Optional[int]
    yettowin: Optional[int]
    actualvsexpectations: Optional[int]
    champion: Optional[bool]
    team_overallrating: Optional[int]
    team_attackrating: Optional[int]
    team_midfieldrating: Optional[int]
    team_defenserating: Optional[int]
    buildupplay: Optional[int]
    defensivedepth: Optional[int]

    @classmethod
    def from_row(cls, row: pd.Series) -> "SeasonOverview":
        return cls(
            export_date=str(row["export_date"]),
            season_year=int(row["season_year"]),
            user_teamid=int(row["user_teamid"]),
            user_teamname=_opt_str(row.get("user_teamname")),
            leagueid=int(row["leagueid"]),
            leaguename=_opt_str(row.get("leaguename")),
            league_level=_opt_int(row.get("league_level")),
            leaguetype=_opt_int(row.get("leaguetype")),
            currenttableposition=_opt_int(row.get("currenttableposition")),
            previousyeartableposition=_opt_int(row.get("previousyeartableposition")),
            points=int(row["points"]),
            nummatchesplayed=int(row["nummatchesplayed"]),
            homewins=_opt_int(row.get("homewins")),
            homedraws=_opt_int(row.get("homedraws")),
            homelosses=_opt_int(row.get("homelosses")),
            awaywins=_opt_int(row.get("awaywins")),
            awaydraws=_opt_int(row.get("awaydraws")),
            awaylosses=_opt_int(row.get("awaylosses")),
            homegf=_opt_int(row.get("homegf")),
            homega=_opt_int(row.get("homega")),
            awaygf=_opt_int(row.get("awaygf")),
            awayga=_opt_int(row.get("awayga")),
            teamform=_opt_str(row.get("teamform")),
            teamshortform=_opt_str(row.get("teamshortform")),
            teamlongform=_opt_str(row.get("teamlongform")),
            lastgameresult=_opt_int(row.get("lastgameresult")),
            unbeatenhome=_opt_int(row.get("unbeatenhome")),
            unbeatenaway=_opt_int(row.get("unbeatenaway")),
            unbeatenleague=_opt_int(row.get("unbeatenleague")),
            unbeatenallcomps=_opt_int(row.get("unbeatenallcomps")),
            objective=_opt_int(row.get("objective")),
            hasachievedobjective=_opt_bool(row.get("hasachievedobjective")),
            highestpossible=_opt_int(row.get("highestpossible")),
            highestprobable=_opt_int(row.get("highestprobable")),
            yettowin=_opt_int(row.get("yettowin")),
            actualvsexpectations=_opt_int(row.get("actualvsexpectations")),
            champion=_opt_bool(row.get("champion")),
            team_overallrating=_opt_int(row.get("team_overallrating")),
            team_attackrating=_opt_int(row.get("team_attackrating")),
            team_midfieldrating=_opt_int(row.get("team_midfieldrating")),
            team_defenserating=_opt_int(row.get("team_defenserating")),
            buildupplay=_opt_int(row.get("buildupplay")),
            defensivedepth=_opt_int(row.get("defensivedepth")),
        )


def from_dataframe(df: pd.DataFrame) -> list[SeasonOverview]:
    return [SeasonOverview.from_row(row) for _, row in df.iterrows()]


__all__ = ["SeasonOverview", "from_dataframe"]
