import os
from celery import Celery

# Celery 配置
redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

# 我们直接在这里定义 app，并指定包含任务的模块
# 'tasks' 会让 Celery 寻找一个名为 tasks.py 的文件来加载任务
celery_app = Celery(
    "worker",
    broker=redis_url,
    backend=redis_url,
    include=["tasks"],  # 直接指定包含任务的模块
)

# 可选：配置其他 Celery 设置
celery_app.conf.update(
    task_track_started=True,
) 