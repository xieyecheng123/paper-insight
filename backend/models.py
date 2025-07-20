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
    filename: str = Field(index=True) # 用于存储服务器上的唯一文件名 (UUID)
    original_filename: str # 用于存储用户上传的原始文件名
    status: PaperStatus = Field(default=PaperStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    analysis: Optional["Analysis"] = Relationship(back_populates="paper")


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


# Pydantic 模型用于 API 响应，避免循环引用问题
class AnalysisRead(SQLModel):
    title: str
    exec_summary: str
    background: str
    methods: str
    results: str
    discussion: str
    quick_ref: str

class PaperWithAnalysis(SQLModel):
    paper_id: int
    filename: str # 在 API 层面，我们返回原始文件名
    status: PaperStatus
    analysis: Optional[AnalysisRead] = None 