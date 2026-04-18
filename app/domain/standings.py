"""Standings row domain object matching PT §7.2 STANDINGS columns."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from app.domain.player import _opt_bool, _opt_int, _opt_str


@dataclass
class StandingsRow:
    export_date: str
    leagueid: int
    leaguename: Optional[str]
    teamid: int
    teamname: Optional[str]
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
    teamlongform: Optional[str]
    lastgameresult: Optional[int]
    unbeatenleague: Optional[int]
    champion: Optional[bool]
    team_overallrating: Optional[int]

    @classmethod
    def from_row(cls, row: pd.Series) -> "StandingsRow":
        return cls(
            export_date=str(row["export_date"]),
            leagueid=int(row["leagueid"]),
            leaguename=_opt_str(row.get("leaguename")),
            teamid=int(row["teamid"]),
            teamname=_opt_str(row.get("teamname")),
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
            teamlongform=_opt_str(row.get("teamlongform")),
            lastgameresult=_opt_int(row.get("lastgameresult")),
            unbeatenleague=_opt_int(row.get("unbeatenleague")),
            champion=_opt_bool(row.get("champion")),
            team_overallrating=_opt_int(row.get("team_overallrating")),
        )


def from_dataframe(df: pd.DataFrame) -> list[StandingsRow]:
    return [StandingsRow.from_row(row) for _, row in df.iterrows()]


__all__ = ["StandingsRow", "from_dataframe"]
