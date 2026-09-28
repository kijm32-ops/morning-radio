from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceName = Literal["world", "morning", "ptis"]
SourceStatus = Literal["ok", "degraded", "failed"]
TurnKind = Literal[
    "fact",
    "analysis",
    "hypothesis",
    "counterpoint",
    "transition",
    "watchpoint",
]
Speaker = Literal["A", "B"]


class SourceDocument(BaseModel):
    source: SourceName
    title: str
    captured_at: datetime
    status: SourceStatus = "ok"
    text: str
    origin: str = ""


class PodcastTurn(BaseModel):
    speaker: Speaker
    kind: TurnKind
    text: str = Field(min_length=1)
    style: str = "natural, conversational Korean"
    evidence: list[str] = Field(default_factory=list)


class PodcastSegment(BaseModel):
    title: str
    turns: list[PodcastTurn] = Field(min_length=2)


class EpisodePlan(BaseModel):
    date: str
    title: str
    teaser: str
    target_minutes: int = Field(ge=8, le=35)
    segments: list[PodcastSegment] = Field(min_length=3, max_length=8)
    watchpoints: list[str] = Field(default_factory=list)
    source_notes: list[str] = Field(default_factory=list)

    @property
    def all_turns(self) -> list[PodcastTurn]:
        return [turn for segment in self.segments for turn in segment.turns]
