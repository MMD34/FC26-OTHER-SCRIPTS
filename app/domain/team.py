"""Team extract (subset of PT §7.1/§7.2 team-level columns)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from app.domain.player import _opt_int, _opt_str


@dataclass
class Team:
    teamid: int
    teamname: Optional[str]
    overallrating: Optional[int]

    @classmethod
    def from_row(cls, row: pd.Series) -> "Team":
        return cls(
            teamid=int(row["teamid"]),
            teamname=_opt_str(row.get("teamname")),
            overallrating=_opt_int(
                row.get("team_overallrating", row.get("overallrating"))
            ),
        )


def from_dataframe(df: pd.DataFrame) -> list[Team]:
    return [Team.from_row(row) for _, row in df.iterrows()]


__all__ = ["Team", "from_dataframe"]
