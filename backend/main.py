import os
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from sqlmodel import Session

from celery_worker import celery_app
from db import get_session, init_db
from models import Paper, PaperStatus
from sqlmodel import select
from tasks import summarize_paper_task

# 确保上传目录存在
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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

MAX_FILE_SIZE_MB = 100  # 限制最大为 100MB


@app.post("/api/upload", response_model=Paper)
async def upload_paper(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    try:
        # 安全地处理文件名
        safe_filename = Path(file.filename).name
        file_path = UPLOAD_DIR / safe_filename

        # 将上传的文件保存到磁盘
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # 在数据库中创建论文记录
        paper = Paper(filename=safe_filename, status=PaperStatus.PENDING)
        session.add(paper)
        session.commit()
        session.refresh(paper)

        # 调用 Celery 任务进行异步处理
        summarize_paper_task.delay(paper.id)

        return paper
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")


# 查询论文状态与解析结果
@app.get("/api/paper/{paper_id}") # 添加缺失的 /api 前缀
def get_paper(paper_id: int, session: Session = Depends(get_session)): # 注入 session
    paper = session.get(Paper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    analysis_data = None
    # 确保 analysis 存在且不为空
    if paper.analysis:
        analysis_data = {
            "title": paper.analysis.title,
            "exec_summary": paper.analysis.exec_summary,
            "background": paper.analysis.background,
            "methods": paper.analysis.methods,
            "results": paper.analysis.results,
            "discussion": paper.analysis.discussion,
            "quick_ref": paper.analysis.quick_ref,
        }

    return {
        "paper_id": paper.id,
        "filename": paper.filename,
        "status": paper.status,
        "analysis": analysis_data,
    } 