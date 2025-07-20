import os
import uuid
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from db import get_session, init_db
from models import Paper, PaperStatus, PaperWithAnalysis
from tasks import summarize_paper_task

# 从环境变量加载上传目录，提供一个健壮的默认值
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

# 限制最大文件大小为 100MB
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", 100)) * 1024 * 1024
# 允许的文件内容类型
ALLOWED_CONTENT_TYPES = ["application/pdf"]

# 应用启动时初始化数据库
init_db()

app = FastAPI(title="Paper Insight API")

# Allow all origins for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload", response_model=Paper)
async def upload_paper(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    # 1. 校验文件类型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file.content_type}. 请上传 PDF 文件。"
        )

    # 2. 校验文件大小
    size = await file.read()
    if len(size) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, # 413 Payload Too Large
            detail=f"文件过大，超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制。"
        )
    await file.seek(0) # 重置文件指针，以便后续读取

    try:
        # 使用原始文件名来获取文件扩展名
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # 将已读取并校验过的文件内容写入磁盘
        with open(file_path, "wb") as buffer:
            buffer.write(size)

        # 在数据库中创建论文记录
        paper = Paper(
            filename=unique_filename,
            original_filename=file.filename,
            status=PaperStatus.PENDING
        )
        session.add(paper)
        session.commit()
        session.refresh(paper) # 在这里 refresh 是有用的，因为我们需要包含 id 和 created_at 的完整对象

        # 异步处理任务
        summarize_paper_task.delay(paper.id)

        return paper
    except Exception as e:
        # 更具体的错误日志
        raise HTTPException(status_code=500, detail=f"处理文件时发生内部错误: {e}")


@app.get("/api/paper/{paper_id}", response_model=PaperWithAnalysis)
def get_paper(paper_id: int, session: Session = Depends(get_session)):
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # FastAPI 将自动根据 response_model 来序列化返回值
    # 我们只需构建一个符合 PaperWithAnalysis 结构的字典
    return {
        "paper_id": paper.id,
        "filename": paper.original_filename,
        "status": paper.status,
        "analysis": paper.analysis, # 如果 paper.analysis 为 None, 它也会被正确处理
    } 