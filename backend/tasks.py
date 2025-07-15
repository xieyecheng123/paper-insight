import os
from uuid import uuid4

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai
import json

from celery_worker import celery_app
from db import get_session
from models import Paper, Analysis

# Set OpenAI API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY", "")


@celery_app.task(name="tasks.parse_pdf")
def parse_pdf(pdf_path: str, paper_id: str):
    """Extract text from PDF, chunk, send to LLM, and store result as JSON."""
    try:
        # update paper status to processing
        with get_session() as session:
            paper = session.get(Paper, int(paper_id))
            if paper:
                paper.status = "processing"
                session.add(paper)
                session.commit()

        # 1. Extract text
        reader = PdfReader(pdf_path)
        full_text = "\n".join(page.extract_text() or "" for page in reader.pages)

        # 2. Split into manageable chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
        chunks = splitter.split_text(full_text)

        # 3. Build prompt (simplified – you can expand with your rules)
        SYSTEM_PROMPT = (
            "你是一位专业的学术论文解析专家。请根据给定的论文内容，输出 JSON，字段包括: "
            "exec_summary, background, methods, results, discussion, quick_ref。要求中文输出。"
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n\n".join(chunks)},
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # 如需更高质量可换成 gpt-4o
            messages=messages,
            temperature=0.2,
        )
        result_content = response.choices[0].message.content

        # After obtaining result_content (assumed JSON string), parse JSON
        try:
            data = json.loads(result_content)
        except json.JSONDecodeError:
            data = {}

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
        return {"status": "error", "paper_id": paper_id, "error": str(e)} 