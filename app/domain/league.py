"""League extract (subset of PT §7.1/§7.2 league-level columns)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from app.domain.player import _opt_int, _opt_str


@dataclass
class League:
    leagueid: int
    leaguename: Optional[str]
    level: Optional[int]

    @classmethod
    def from_row(cls, row: pd.Series) -> "League":
        return cls(
            leagueid=int(row["leagueid"]),
            leaguename=_opt_str(row.get("leaguename")),
            level=_opt_int(row.get("league_level", row.get("level"))),
        )


def from_dataframe(df: pd.DataFrame) -> list[League]:
    return [League.from_row(row) for _, row in df.iterrows()]


__all__ = ["League", "from_dataframe"]
