# Paper Insight

使用 FastAPI, Next.js 和 Celery 构建的论文解析与洞察应用。用户可上传 PDF 格式的学术论文，系统将通过 AI 对其进行分析，并提供结构化的摘要与解读。

## 技术栈

- **后端**: Python, FastAPI, Celery, SQLModel (SQLite), OpenAI
- **前端**: Next.js (App Router), TypeScript, Tailwind CSS
- **基础设施**: Docker, Docker Compose, Redis

## 环境准备

1.  **Docker**: 请确保本地已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。
2.  **Git**: 确认 Git 已安装。
3.  **OpenAI API Key**: 需要一个有效的 OpenAI API Key，并确保其有 `gpt-4o-mini` 或更高版本模型的访问权限。

## 快速启动（开发环境）

1.  **克隆仓库**
    ```bash
    git clone <your-repo-url>
    cd paper-insight
    ```

2.  **配置环境变量**
    -   复制后端环境变量示例文件：
        ```bash
        cp backend/env.example backend/.env
        ```
    -   编辑 `backend/.env`，填入你的 OpenAI API Key:
        ```
        OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        ```

3.  **启动服务**
    使用 Docker Compose 一键构建并启动所有服务：
    ```bash
    docker compose up --build -d
    ```

4.  **访问应用**
    -   **前端**: [http://localhost:3000](http://localhost:3000)
    -   **后端 API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 生产环境启动

如果你需要以生产模式运行（更小的镜像体积，无代码热更新），请使用 `docker-compose.prod.yml`:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

## API 端点

-   `POST /upload`: 上传 PDF 文件。返回 `task_id` 和 `paper_id`。
-   `GET /paper/{paper_id}`: 根据论文 ID 查询解析状态与结果。

## 停止服务

```bash
docker compose down
``` 