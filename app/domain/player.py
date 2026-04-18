"""Player domain object matching PT §7.3 PLAYERS_SNAPSHOT columns."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


def _opt_int(v) -> Optional[int]:
    if v is None or pd.isna(v):
        return None
    return int(v)


def _opt_str(v) -> Optional[str]:
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return str(v)


def _opt_bool(v) -> Optional[bool]:
    if v is None or pd.isna(v):
        return None
    return bool(v)


@dataclass
class Player:
    export_date: str
    playerid: int
    is_generated: Optional[bool]
    display_name: Optional[str]
    firstname: Optional[str]
    lastname: Optional[str]
    commonname: Optional[str]
    jerseyname: Optional[str]
    birthdate: Optional[int]
    age: Optional[int]
    nationality: Optional[int]
    gender: Optional[int]
    preferredfoot: Optional[int]
    preferredposition1: Optional[int]
    overallrating: Optional[int]
    potential: Optional[int]
    pacdiv: Optional[int]
    shohan: Optional[int]
    paskic: Optional[int]
    driref: Optional[int]
    defspe: Optional[int]
    phypos: Optional[int]
    teamid: Optional[int]
    teamname: Optional[str]
    leagueid: Optional[int]
    leaguename: Optional[str]
    league_level: Optional[int]
    form: Optional[int]
    injury: Optional[int]
    leagueappearances: Optional[int]
    leaguegoals: Optional[int]
    yellows: Optional[int]
    reds: Optional[int]
    contractvaliduntil: Optional[int]

    @classmethod
    def from_row(cls, row: pd.Series) -> "Player":
        return cls(
            export_date=str(row["export_date"]),
            playerid=int(row["playerid"]),
            is_generated=_opt_bool(row.get("is_generated")),
            display_name=_opt_str(row.get("display_name")),
            firstname=_opt_str(row.get("firstname")),
            lastname=_opt_str(row.get("lastname")),
            commonname=_opt_str(row.get("commonname")),
            jerseyname=_opt_str(row.get("jerseyname")),
            birthdate=_opt_int(row.get("birthdate")),
            age=_opt_int(row.get("age")),
            nationality=_opt_int(row.get("nationality")),
            gender=_opt_int(row.get("gender")),
            preferredfoot=_opt_int(row.get("preferredfoot")),
            preferredposition1=_opt_int(row.get("preferredposition1")),
            overallrating=_opt_int(row.get("overallrating")),
            potential=_opt_int(row.get("potential")),
            pacdiv=_opt_int(row.get("pacdiv")),
            shohan=_opt_int(row.get("shohan")),
            paskic=_opt_int(row.get("paskic")),
            driref=_opt_int(row.get("driref")),
            defspe=_opt_int(row.get("defspe")),
            phypos=_opt_int(row.get("phypos")),
            teamid=_opt_int(row.get("teamid")),
            teamname=_opt_str(row.get("teamname")),
            leagueid=_opt_int(row.get("leagueid")),
            leaguename=_opt_str(row.get("leaguename")),
            league_level=_opt_int(row.get("league_level")),
            form=_opt_int(row.get("form")),
            injury=_opt_int(row.get("injury")),
            leagueappearances=_opt_int(row.get("leagueappearances")),
            leaguegoals=_opt_int(row.get("leaguegoals")),
            yellows=_opt_int(row.get("yellows")),
            reds=_opt_int(row.get("reds")),
            contractvaliduntil=_opt_int(row.get("contractvaliduntil")),
        )


def from_dataframe(df: pd.DataFrame) -> list[Player]:
    return [Player.from_row(row) for _, row in df.iterrows()]


__all__ = ["Player", "from_dataframe"]
