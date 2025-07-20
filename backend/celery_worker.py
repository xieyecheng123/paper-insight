import os
import redis
from celery_app import celery_app
# 导入任务模块以确保 Celery worker 能够发现它们
import tasks

# 这个文件现在只是一个入口点，用于启动 Celery worker。
# `celery_app.py` 中已经配置了自动发现任务，
# 并且通过 `import tasks`，我们确保了任务在 worker 启动时被加载和注册。