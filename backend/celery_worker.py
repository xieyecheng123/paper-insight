from celery import Celery
from db import init_db

# Broker and backend point to the Redis service defined in docker-compose
celery_app = Celery(
    "paper_insight",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

# 直接导入 tasks 模块以确保任务被注册
import importlib

try:
    importlib.import_module("tasks")
except ModuleNotFoundError:
    # 在开发阶段打印提示而不中断运行
    print("Warning: tasks module not found; celery worker will not process tasks.")

init_db() 