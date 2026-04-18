"""Transfer history row matching PT §7.7 TRANSFER_HISTORY columns."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from app.domain.player import _opt_int, _opt_str


@dataclass
class Transfer:
    type: Optional[str]
    date: Optional[str]
    playerid: int
    exchangeplayerid: Optional[int]
    teamfromid: Optional[int]
    teamtoid: Optional[int]
    playername: Optional[str]
    exchangeplayername: Optional[str]
    teamfromname: Optional[str]
    teamtoname: Optional[str]
    fee: Optional[int]
    total_deal_value: Optional[int]

    @classmethod
    def from_row(cls, row: pd.Series) -> "Transfer":
        return cls(
            type=_opt_str(row.get("type")),
            date=_opt_str(row.get("date")),
            playerid=int(row["playerid"]),
            exchangeplayerid=_opt_int(row.get("exchangeplayerid")),
            teamfromid=_opt_int(row.get("teamfromid")),
            teamtoid=_opt_int(row.get("teamtoid")),
            playername=_opt_str(row.get("playername")),
            exchangeplayername=_opt_str(row.get("exchangeplayername")),
            teamfromname=_opt_str(row.get("teamfromname")),
            teamtoname=_opt_str(row.get("teamtoname")),
            fee=_opt_int(row.get("fee")),
            total_deal_value=_opt_int(row.get("total_deal_value")),
        )


def from_dataframe(df: pd.DataFrame) -> list[Transfer]:
    return [Transfer.from_row(row) for _, row in df.iterrows()]


__all__ = ["Transfer", "from_dataframe"]
