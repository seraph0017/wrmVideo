#!/bin/bash
# Celery快速启动脚本
# 用于快速启动Celery服务
#
# 版本: v2.0
# 更新内容:
#   - 添加定时任务列表查看功能 (tasks)
#   - 添加日志查看功能 (logs)
#   - 添加数据库扫描任务测试功能 (test)
#   - 自动创建和检查日志目录
#   - 支持scan_database_celery_tasks定时任务
#
# 使用方法:
#     ./start_celery.sh worker     # 启动worker
#     ./start_celery.sh beat       # 启动beat
#     ./start_celery.sh both       # 同时启动worker和beat
#     ./start_celery.sh status     # 查看状态
#     ./start_celery.sh tasks      # 查看定时任务列表
#     ./start_celery.sh logs       # 查看日志
#     ./start_celery.sh test       # 测试数据库扫描任务
#     ./start_celery.sh stop       # 停止所有Celery进程

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 检查Python环境
check_python() {
    if ! command -v python &> /dev/null; then
        echo -e "${RED}错误: 未找到Python${NC}"
        exit 1
    fi
    
    # 设置Django环境变量
    export DJANGO_SETTINGS_MODULE=web.settings
    
    # 检查Django设置
    if ! python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings'); import django; django.setup()" 2>/dev/null; then
        echo -e "${RED}错误: Django环境设置失败${NC}"
        echo -e "${YELLOW}请确保在web目录下运行此脚本${NC}"
        exit 1
    fi
}

# 检查Redis连接
check_redis() {
    echo -e "${BLUE}检查Redis连接...${NC}"
    if ! python -c "import redis; r=redis.Redis(host='localhost', port=6379, db=0); r.ping()" 2>/dev/null; then
        echo -e "${RED}警告: Redis连接失败，请确保Redis服务正在运行${NC}"
        echo -e "${YELLOW}启动Redis: brew services start redis${NC}"
    else
        echo -e "${GREEN}✅ Redis连接正常${NC}"
    fi
}

# 检查并创建日志目录
check_logs_dir() {
    if [ ! -d "logs" ]; then
        echo -e "${YELLOW}创建日志目录...${NC}"
        mkdir -p logs
    fi
    
    # 检查日志文件权限
    if [ -f "logs/celery.log" ] && [ ! -w "logs/celery.log" ]; then
        echo -e "${YELLOW}修复日志文件权限...${NC}"
        chmod 644 logs/celery.log
    fi
}

# 启动worker
start_worker() {
    echo -e "${GREEN}启动Celery Worker...${NC}"
    python run_celery.py worker --loglevel info
}

# 启动beat
start_beat() {
    echo -e "${GREEN}启动Celery Beat调度器...${NC}"
    python run_celery.py beat --loglevel info
}

# 同时启动worker和beat
start_both() {
    echo -e "${GREEN}同时启动Celery Worker和Beat调度器...${NC}"
    python run_celery.py both --loglevel info
}

# 查看状态
show_status() {
    echo -e "${BLUE}Celery状态检查${NC}"
    python run_celery.py status
}

# 停止所有Celery进程
stop_celery() {
    echo -e "${YELLOW}停止所有Celery进程...${NC}"
    
    # 查找并停止celery进程
    CELERY_PIDS=$(pgrep -f "celery.*worker\|celery.*beat")
    
    if [ -z "$CELERY_PIDS" ]; then
        echo -e "${GREEN}没有运行的Celery进程${NC}"
    else
        echo -e "${YELLOW}找到Celery进程: $CELERY_PIDS${NC}"
        echo "$CELERY_PIDS" | xargs kill -TERM
        sleep 2
        
        # 检查是否还有进程在运行
        REMAINING_PIDS=$(pgrep -f "celery.*worker\|celery.*beat")
        if [ ! -z "$REMAINING_PIDS" ]; then
            echo -e "${RED}强制停止剩余进程: $REMAINING_PIDS${NC}"
            echo "$REMAINING_PIDS" | xargs kill -KILL
        fi
        
        echo -e "${GREEN}✅ Celery进程已停止${NC}"
    fi
}

# 清空队列
purge_queue() {
    echo -e "${YELLOW}清空Celery任务队列...${NC}"
    python run_celery.py purge
}

# 查看定时任务列表
show_tasks() {
    echo -e "${BLUE}Celery定时任务列表${NC}"
    python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
import django
django.setup()
from django_celery_beat.models import PeriodicTask
from django.utils import timezone

tasks = PeriodicTask.objects.all()
print(f'共有 {tasks.count()} 个定时任务:')
print('-' * 80)
for task in tasks:
    status = '✅ 启用' if task.enabled else '❌ 禁用'
    last_run = task.last_run_at.strftime('%Y-%m-%d %H:%M:%S') if task.last_run_at else '从未运行'
    print(f'{status} {task.name}')
    print(f'    任务: {task.task}')
    print(f'    间隔: {task.interval}')
    print(f'    上次运行: {last_run}')
    print()
"
}

# 查看任务日志
show_logs() {
    echo -e "${BLUE}查看Celery日志${NC}"
    if [ -f "logs/celery.log" ]; then
        echo -e "${YELLOW}最近50行日志:${NC}"
        tail -50 logs/celery.log
        echo ""
        echo -e "${YELLOW}实时日志监控 (Ctrl+C退出):${NC}"
        tail -f logs/celery.log
    else
        echo -e "${RED}日志文件不存在: logs/celery.log${NC}"
    fi
}

# 测试数据库扫描任务
test_scan_task() {
    echo -e "${BLUE}测试数据库扫描任务${NC}"
    python manage.py shell -c "
from video.tasks import scan_database_celery_tasks
print('开始执行数据库扫描任务...')
result = scan_database_celery_tasks()
print('任务执行完成:')
print(f'结果: {result}')
"
}

# 显示帮助
show_help() {
    echo -e "${BLUE}Celery快速启动脚本${NC}"
    echo ""
    echo "使用方法:"
    echo "  $0 worker     启动Celery Worker"
    echo "  $0 beat       启动Celery Beat调度器"
    echo "  $0 both       同时启动Worker和Beat"
    echo "  $0 status     查看Celery状态"
    echo "  $0 stop       停止所有Celery进程"
    echo "  $0 purge      清空任务队列"
    echo "  $0 tasks      查看定时任务列表"
    echo "  $0 logs       查看Celery日志"
    echo "  $0 test       测试数据库扫描任务"
    echo "  $0 help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 both       # 最常用：同时启动worker和beat"
    echo "  $0 status     # 检查服务状态"
    echo "  $0 tasks      # 查看定时任务配置"
    echo "  $0 logs       # 查看运行日志"
    echo "  $0 test       # 测试数据库扫描功能"
    echo "  $0 stop       # 停止所有服务"
}

# 主逻辑
case "$1" in
    worker)
        check_python
        check_redis
        check_logs_dir
        start_worker
        ;;
    beat)
        check_python
        check_redis
        check_logs_dir
        start_beat
        ;;
    both)
        check_python
        check_redis
        check_logs_dir
        start_both
        ;;
    status)
        check_python
        show_status
        ;;
    stop)
        stop_celery
        ;;
    purge)
        check_python
        purge_queue
        ;;
    tasks)
        check_python
        show_tasks
        ;;
    logs)
        show_logs
        ;;
    test)
        check_python
        test_scan_task
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo -e "${RED}错误: 请指定命令${NC}"
        show_help
        exit 1
        ;;
    *)
        echo -e "${RED}错误: 未知命令 '$1'${NC}"
        show_help
        exit 1
        ;;
esac