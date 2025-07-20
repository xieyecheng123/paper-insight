import os
import json
import traceback
from logging import getLogger

from pypdf import PdfReader
import google.generativeai as genai
from sqlalchemy.orm import Session
from celery.exceptions import MaxRetriesExceededError

from celery_app import celery_app
from db import get_session_for_task, engine
from models import Paper, PaperStatus, Analysis
from sqlalchemy import select

# 获取一个 logger 实例，用于更规范的日志记录
logger = getLogger(__name__)

# 配置 Gemini API
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    # 在应用启动时就明确失败，而不是在任务运行时
    logger.error("FATAL: GOOGLE_API_KEY environment variable not set.")
    raise RuntimeError("GOOGLE_API_KEY environment variable not set.")

def update_paper_status(paper_id: int, status: PaperStatus, session: Session):
    """一个独立的函数，专门用于更新论文状态，增强代码复用性。"""
    paper = session.get(Paper, paper_id)
    if paper:
        paper.status = status
        session.add(paper)
        session.commit()
    else:
        logger.warning(f"Attempted to update status for non-existent paper_id: {paper_id}")

@celery_app.task(
    bind=True, 
    autoretry_for=(Exception,), 
    retry_kwargs={'max_retries': 3, 'countdown': 5}
)
def summarize_paper_task(self, paper_id: int):
    """
    Celery task to summarize a paper.
    This task will automatically retry up to 3 times on failure.
    """
    logger.info(f"Starting summarize_paper_task for paper_id: {paper_id}")

    # 使用一个新的 session 来确保事务的隔离性
    with Session(engine) as session:
        try:
            paper = session.get(Paper, paper_id)
            if not paper:
                logger.error(f"Paper with ID {paper_id} not found in task.")
                return

            # 1. 立即更新状态为 PROCESSING，并提交事务
            # 这是一个独立的、快速的事务，让前端可以马上看到变化
            paper.status = PaperStatus.PROCESSING
            session.add(paper)
            session.commit()
            logger.info(f"Paper {paper_id} status updated to PROCESSING.")

            # 2. 从磁盘读取 PDF 内容
            file_path = os.path.join("/app/uploads", paper.filename)
            logger.info(f"Reading file: {file_path}")
            reader = PdfReader(file_path)
            full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if not full_text.strip():
                raise ValueError("Extracted text from PDF is empty.")

            # 3. 调用 AI 模型进行分析
            SYSTEM_PROMPT = (
                 "你是一位专业的学术论文解析专家。请根据以下论文内容，返回一个合法的 JSON 对象，不要包含任何 markdown 语法 (```json ... ```)。"
                "JSON 对象应包含以下字段: "
                "'title' (论文的官方标题，如果原文是英文，请翻译成中文), "
                "'exec_summary' (执行摘要), "
                "'background' (研究背景与动机), "
                "'methods' (核心概念与方法), "
                "'results' (实验与结果分析), "
                "'discussion' (讨论与评价), "
                "'quick_ref' (关键信息快速参考)。"
                "确保所有字段的值都是字符串，并且内容为中文。"
                "\n\n论文内容如下:\n\n"
            )
            prompt = SYSTEM_PROMPT + full_text
            
            logger.info(f"Generating content for paper_id: {paper_id}")
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)

            # 4. 在一个事务中完成所有数据库写入操作
            logger.info(f"Saving analysis for paper_id: {paper_id}")
            
            # 使用 get() 来查找，如果不存在则创建
            analysis = session.get(Analysis, paper.id) or Analysis(paper_id=paper.id)

            analysis.title=data.get("title", "标题未找到")
            analysis.exec_summary=data.get("exec_summary", "")
            analysis.background=data.get("background", "")
            analysis.methods=data.get("methods", "")
            analysis.results=data.get("results", "")
            analysis.discussion=data.get("discussion", "")
            analysis.quick_ref=data.get("quick_ref", "")
            
            session.add(analysis)
            
            paper.status = PaperStatus.COMPLETED
            session.add(paper)

            session.commit()
            logger.info(f"Successfully processed and saved paper_id: {paper_id}")
            return {"status": "completed", "paper_id": paper_id}

        except Exception as e:
            logger.error(f"An error occurred in summarize_paper_task for paper_id: {paper_id}", exc_info=True)
            # 回滚当前事务，以防部分数据被写入
            session.rollback()
            # 标记为失败状态
            with Session(engine) as error_session:
                update_paper_status(paper_id, PaperStatus.FAILED, error_session)
            # 重新抛出异常，以便 Celery 的重试机制能够捕获它
            raise 