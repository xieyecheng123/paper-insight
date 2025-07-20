#!/bin/sh
# entrypoint.sh

set -e

# 等待 PostgreSQL 启动
# 使用 pg_isready 工具检查 PostgreSQL 服务是否准备好接受连接
# -h postgres: 指定要连接的主机名，这里是我们的 postgres 服务容器
# -U "${POSTGRES_USER}": 指定连接数据库时使用的用户名，从环境变量中读取
# -q: 安静模式，如果连接成功则不输出任何信息
# "|| exit 1": 如果 pg_isready 命令失败（返回非零退出码），则立即退出脚本
until pg_isready -h postgres -U "${POSTGRES_USER}" -q; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

# >&2 echo ...: 将消息输出到标准错误流，方便在日志中区分常规输出和错误信息
>&2 echo "PostgreSQL is up - executing command"

# 等待数据库准备好之后，执行传递给脚本的原始命令
# exec "$@": 使用 exec 可以让子进程（这里是 uvicorn）替换当前的 shell 进程，
# 这样可以正确地接收和处理来自 Docker 的信号（例如，docker-compose stop）
exec "$@" 