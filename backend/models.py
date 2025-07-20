from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class PaperStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Paper(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    status: PaperStatus = Field(default=PaperStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    analysis: "Analysis" = Relationship(back_populates="paper")


class Analysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    title: str = Field(default="")
    exec_summary: str
    background: str
    methods: str
    results: str
    discussion: str
    quick_ref: str

    paper: Paper = Relationship(back_populates="analysis") 