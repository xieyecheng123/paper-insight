import os
import json
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai

from celery_app import celery_app
from db import get_session_for_task
from models import Paper, PaperStatus, Analysis
from sqlalchemy import select

# Configure the Gemini API key from environment variables
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    # This will be caught by the task's exception handler
    raise RuntimeError("GOOGLE_API_KEY environment variable not set.")


@celery_app.task(name="summarize_paper_task")
def summarize_paper_task(paper_id: int):
    """
    Celery task to summarize a paper.
    """
    with get_session_for_task() as session:
        try:
            # 1. Update paper status to PROCESSING
            paper = session.get(Paper, paper_id)
            if not paper:
                print(f"Error: Paper with ID {paper_id} not found.")
                return
            paper.status = PaperStatus.PROCESSING
            session.add(paper)
            session.commit()
            session.refresh(paper)

            # 2. Get the content of the paper
            file_path = os.path.join("/app/uploads", paper.filename)
            reader = PdfReader(file_path)
            full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

            # 3. Create analysis
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

            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            result_content = response.text

            # 4. Save analysis to database
            data = json.loads(result_content)
            
            # 检查是否已存在对此论文的分析
            existing_analysis = session.exec(select(Analysis).where(Analysis.paper_id == paper_id)).first()
            if existing_analysis:
                analysis = existing_analysis
            else:
                analysis = Analysis(paper_id=paper_id)

            analysis.title=data.get("title", "标题未找到")
            analysis.exec_summary=data.get("exec_summary", "")
            analysis.background=data.get("background", "")
            analysis.methods=data.get("methods", "")
            analysis.results=data.get("results", "")
            analysis.discussion=data.get("discussion", "")
            analysis.quick_ref=data.get("quick_ref", "")
            
            session.add(analysis)
            
            # 5. Update paper status to COMPLETED
            paper = session.get(Paper, paper_id)
            paper.status = PaperStatus.COMPLETED
            session.add(paper)

            session.commit()
            return {"status": "completed", "paper_id": paper_id}
        
        except Exception as e:
            # 使用 print 直接输出错误，确保能被日志捕获
            print(f"!!!!!!!!!! FATAL ERROR IN CELERY TASK !!!!!!!!!!")
            import traceback
            print(traceback.format_exc())
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            
            # 回滚以防 session 处于不良状态
            session.rollback()

            # 再次尝试用一个新的 session 来更新状态
            with get_session_for_task() as error_session:
                paper_to_fail = error_session.get(Paper, paper_id)
                if paper_to_fail:
                    paper_to_fail.status = PaperStatus.FAILED
                    error_session.add(paper_to_fail)
                    error_session.commit() 