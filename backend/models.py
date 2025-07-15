from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Paper(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    status: str = "pending"  # pending | processing | completed | error
    created_at: datetime = Field(default_factory=datetime.utcnow)

    analysis: "Analysis" = Relationship(back_populates="paper")


class Analysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.id")

    exec_summary: str
    background: str
    methods: str
    results: str
    discussion: str
    quick_ref: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    paper: Paper = Relationship(back_populates="analysis") 