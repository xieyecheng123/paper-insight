import os
import json
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import google.generativeai as genai

from celery_worker import celery_app
from db import get_session
from models import Paper, Analysis

# Configure the Gemini API key from environment variables
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    # This will be caught by the task's exception handler
    raise RuntimeError("GOOGLE_API_KEY environment variable not set.")


@celery_app.task(name="tasks.parse_pdf")
def parse_pdf(pdf_path: str, paper_id: str):
    """Extract text from PDF, chunk, send to Gemini, and store result as JSON."""
    try:
        with get_session() as session:
            paper = session.get(Paper, int(paper_id))
            if paper:
                paper.status = "processing"
                session.add(paper)
                session.commit()

        # 1. Extract text
        reader = PdfReader(pdf_path)
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

        # 2. Split into manageable chunks if needed (or send the whole text)
        # For many models, sending the full text is fine if it's within context limits.
        # We will send the full text directly.

        # 3. Build prompt
        SYSTEM_PROMPT = (
            "你是一位专业的学术论文解析专家。请根据以下论文内容，返回一个合法的 JSON 对象，不要包含任何 markdown 语法 (```json ... ```)。"
            "JSON 对象应包含以下字段: "
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

        # 4. Call Gemini API
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        result_content = response.text

        # 5. Parse and store result
        data = json.loads(result_content)
        with get_session() as session:
            analysis = Analysis(
                paper_id=int(paper_id),
                exec_summary=data.get("exec_summary", ""),
                background=data.get("background", ""),
                methods=data.get("methods", ""),
                results=data.get("results", ""),
                discussion=data.get("discussion", ""),
                quick_ref=data.get("quick_ref", ""),
            )
            session.add(analysis)
            paper = session.get(Paper, int(paper_id))
            if paper:
                paper.status = "completed"
            session.commit()

        return {"status": "completed", "paper_id": paper_id}
    except Exception as e:
        with get_session() as session:
            paper = session.get(Paper, int(paper_id))
            if paper:
                paper.status = "error"
            session.commit()
        # Log the actual error for easier debugging
        return {"status": "error", "paper_id": paper_id, "error": str(e)} 