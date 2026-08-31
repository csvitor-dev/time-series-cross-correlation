from __future__ import annotations

from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class OHLCBar(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    source_id: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("source_id", "sourceId")
    )
    ingested_at: Optional[int] = Field(
        default=None, validation_alias=AliasChoices("ingested_at", "ingestedAt")
    )

    time: int
    time_utc: str = Field(validation_alias=AliasChoices("time_utc", "timeUtc"))
    time_sp: str = Field(validation_alias=AliasChoices("time_sp", "timeSp"))
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = Field(validation_alias=AliasChoices("tick_volume", "tickVolume"))
    spread: int
    real_volume: int = Field(validation_alias=AliasChoices("real_volume", "realVolume"))


class OHLCRequest(BaseModel):
    symbol: str
    timeframe: str
    start_time: int
    end_time: int
    limit: int = 1000
    offset: int = 0
    order_desc: bool = True

    def as_query(self) -> dict[str, str]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "limit": str(self.limit),
            "offset": str(self.offset),
            "order_desc": str(self.order_desc).lower(),
        }
