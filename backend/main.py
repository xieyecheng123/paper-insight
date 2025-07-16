from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import os

from celery_worker import celery_app
from db import init_db, get_session
from models import Paper
from sqlmodel import select

app = FastAPI(title="Paper Insight API")

# Allow all origins for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE_MB = 20  # 限制最大为 20MB

init_db()


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """Receive PDF from client, check size, store it, queue Celery task, return paper_id."""
    # 检查文件大小
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail=f"文件过大，请上传小于 {MAX_FILE_SIZE_MB}MB 的 PDF。"
        )

    task_id = str(uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}.pdf")

    with open(file_path, "wb") as out_file:
        out_file.write(await file.read())

    # create Paper record
    with get_session() as session:
        paper = Paper(filename=file.filename, status="pending")
        session.add(paper)
        session.commit()
        session.refresh(paper)

    # send async task with paper_id
    celery_app.send_task("tasks.parse_pdf", args=[file_path, str(paper.id)])

    return {"paper_id": paper.id}


# 查询论文状态与解析结果
@app.get("/paper/{paper_id}")
def get_paper(paper_id: int):
    with get_session() as session:
        paper = session.get(Paper, paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        analysis_data = None
        if paper.analysis:
            # 兼容一对一或一对多
            analysis_record = None
            if isinstance(paper.analysis, list):
                analysis_record = paper.analysis[0] if paper.analysis else None
            else:
                analysis_record = paper.analysis
            if analysis_record:
                analysis_data = {
                    "exec_summary": analysis_record.exec_summary,
                    "background": analysis_record.background,
                    "methods": analysis_record.methods,
                    "results": analysis_record.results,
                    "discussion": analysis_record.discussion,
                    "quick_ref": analysis_record.quick_ref,
                }

        return {
            "paper_id": paper.id,
            "filename": paper.filename,
            "status": paper.status,
            "analysis": analysis_data,
        } 