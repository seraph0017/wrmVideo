#!/bin/bash
# -*- coding: utf-8 -*-
#
# wrmVideo 服务管理脚本
#
# 功能：
# 1. 启动/停止/重启 Web 服务
# 2. 启动/停止/重启 Celery Worker
# 3. 启动/停止/重启 Celery Beat
# 4. 查看服务状态
# 5. 查看服务日志
#
# 使用方法：
#   bash service_manager.sh [命令] [服务]
#
# 命令：
#   start       启动服务
#   stop        停止服务
#   restart     重启服务
#   status      查看状态
#   logs        查看日志
#
# 服务：
#   web         Web 服务
#   celery      Celery Worker
#   beat        Celery Beat
#   all         所有服务（默认）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="${PROJECT_ROOT}/web"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_DIR="${PROJECT_ROOT}/run"

# PID 文件
WEB_PID="${PID_DIR}/gunicorn.pid"
CELERY_PID="${PID_DIR}/celery_worker.pid"
BEAT_PID="${PID_DIR}/celery_beat.pid"

# 日志文件
WEB_ACCESS_LOG="${LOG_DIR}/gunicorn_access.log"
WEB_ERROR_LOG="${LOG_DIR}/gunicorn_error.log"
CELERY_LOG="${LOG_DIR}/celery_worker.log"
BEAT_LOG="${LOG_DIR}/celery_beat.log"

# 创建必要目录
mkdir -p "${LOG_DIR}"
mkdir -p "${PID_DIR}"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查进程是否运行
is_running() {
    local pid_file=$1
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    
    return 1
}

# 激活 Python 环境
activate_python_env() {
    if command -v conda &> /dev/null; then
        # 使用 Conda
        eval "$(conda shell.bash hook)"
        if conda env list | grep -q "wrmvideo"; then
            conda activate wrmvideo
            log_info "已激活 Conda 环境: wrmvideo"
        else
            log_error "Conda 环境 'wrmvideo' 不存在"
            exit 1
        fi
    elif [ -d "${PROJECT_ROOT}/venv" ]; then
        # 使用 venv
        source "${PROJECT_ROOT}/venv/bin/activate"
        log_info "已激活虚拟环境: venv"
    else
        log_warning "未找到虚拟环境，使用系统 Python"
    fi
}

# 启动 Web 服务
start_web() {
    log_info "启动 Web 服务..."
    
    if is_running "$WEB_PID"; then
        log_warning "Web 服务已在运行中"
        return 0
    fi
    
    cd "$WEB_DIR"
    
    gunicorn web.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 4 \
        --timeout 300 \
        --access-logfile "$WEB_ACCESS_LOG" \
        --error-logfile "$WEB_ERROR_LOG" \
        --pid "$WEB_PID" \
        --daemon
    
    sleep 2
    
    if is_running "$WEB_PID"; then
        log_success "Web 服务启动成功 (PID: $(cat $WEB_PID))"
    else
        log_error "Web 服务启动失败"
        return 1
    fi
}

# 停止 Web 服务
stop_web() {
    log_info "停止 Web 服务..."
    
    if ! is_running "$WEB_PID"; then
        log_warning "Web 服务未运行"
        return 0
    fi
    
    local pid=$(cat "$WEB_PID")
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
        sleep 1
        ((count++))
    done
    
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warning "进程未响应，强制终止..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$WEB_PID"
    log_success "Web 服务已停止"
}

# 启动 Celery Worker
start_celery() {
    log_info "启动 Celery Worker..."
    
    if is_running "$CELERY_PID"; then
        log_warning "Celery Worker 已在运行中"
        return 0
    fi
    
    cd "$WEB_DIR"
    
    celery -A web worker \
        --loglevel=info \
        --concurrency=4 \
        --logfile="$CELERY_LOG" \
        --pidfile="$CELERY_PID" \
        --detach
    
    sleep 2
    
    if is_running "$CELERY_PID"; then
        log_success "Celery Worker 启动成功 (PID: $(cat $CELERY_PID))"
    else
        log_error "Celery Worker 启动失败"
        return 1
    fi
}

# 停止 Celery Worker
stop_celery() {
    log_info "停止 Celery Worker..."
    
    if ! is_running "$CELERY_PID"; then
        log_warning "Celery Worker 未运行"
        return 0
    fi
    
    cd "$WEB_DIR"
    celery -A web control shutdown 2>/dev/null || {
        local pid=$(cat "$CELERY_PID")
        kill -TERM "$pid" 2>/dev/null || true
        
        # 等待进程结束
        local count=0
        while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
            sleep 1
            ((count++))
        done
        
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warning "进程未响应，强制终止..."
            kill -KILL "$pid" 2>/dev/null || true
        fi
    }
    
    rm -f "$CELERY_PID"
    log_success "Celery Worker 已停止"
}

# 启动 Celery Beat
start_beat() {
    log_info "启动 Celery Beat..."
    
    if is_running "$BEAT_PID"; then
        log_warning "Celery Beat 已在运行中"
        return 0
    fi
    
    cd "$WEB_DIR"
    
    celery -A web beat \
        --loglevel=info \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler \
        --logfile="$BEAT_LOG" \
        --pidfile="$BEAT_PID" \
        --detach
    
    sleep 2
    
    if is_running "$BEAT_PID"; then
        log_success "Celery Beat 启动成功 (PID: $(cat $BEAT_PID))"
    else
        log_error "Celery Beat 启动失败"
        return 1
    fi
}

# 停止 Celery Beat
stop_beat() {
    log_info "停止 Celery Beat..."
    
    if ! is_running "$BEAT_PID"; then
        log_warning "Celery Beat 未运行"
        return 0
    fi
    
    local pid=$(cat "$BEAT_PID")
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
        sleep 1
        ((count++))
    done
    
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warning "进程未响应，强制终止..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$BEAT_PID"
    log_success "Celery Beat 已停止"
}

# 查看服务状态
status_web() {
    if is_running "$WEB_PID"; then
        local pid=$(cat "$WEB_PID")
        echo -e "${GREEN}●${NC} Web 服务: 运行中 (PID: $pid)"
    else
        echo -e "${RED}●${NC} Web 服务: 未运行"
    fi
}

status_celery() {
    if is_running "$CELERY_PID"; then
        local pid=$(cat "$CELERY_PID")
        echo -e "${GREEN}●${NC} Celery Worker: 运行中 (PID: $pid)"
    else
        echo -e "${RED}●${NC} Celery Worker: 未运行"
    fi
}

status_beat() {
    if is_running "$BEAT_PID"; then
        local pid=$(cat "$BEAT_PID")
        echo -e "${GREEN}●${NC} Celery Beat: 运行中 (PID: $pid)"
    else
        echo -e "${RED}●${NC} Celery Beat: 未运行"
    fi
}

# 查看日志
logs_web() {
    if [ -f "$WEB_ERROR_LOG" ]; then
        log_info "Web 错误日志 (最近 50 行):"
        tail -n 50 "$WEB_ERROR_LOG"
    else
        log_warning "日志文件不存在: $WEB_ERROR_LOG"
    fi
}

logs_celery() {
    if [ -f "$CELERY_LOG" ]; then
        log_info "Celery Worker 日志 (最近 50 行):"
        tail -n 50 "$CELERY_LOG"
    else
        log_warning "日志文件不存在: $CELERY_LOG"
    fi
}

logs_beat() {
    if [ -f "$BEAT_LOG" ]; then
        log_info "Celery Beat 日志 (最近 50 行):"
        tail -n 50 "$BEAT_LOG"
    else
        log_warning "日志文件不存在: $BEAT_LOG"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
wrmVideo 服务管理脚本

使用方法:
    bash service_manager.sh [命令] [服务]

命令:
    start       启动服务
    stop        停止服务
    restart     重启服务
    status      查看状态
    logs        查看日志

服务:
    web         Web 服务 (Gunicorn)
    celery      Celery Worker
    beat        Celery Beat
    all         所有服务（默认）

示例:
    # 启动所有服务
    bash service_manager.sh start

    # 停止 Web 服务
    bash service_manager.sh stop web

    # 重启 Celery Worker
    bash service_manager.sh restart celery

    # 查看所有服务状态
    bash service_manager.sh status

    # 查看 Web 服务日志
    bash service_manager.sh logs web

EOF
}

# 主函数
main() {
    local command=${1:-status}
    local service=${2:-all}
    
    # 显示帮助
    if [ "$command" = "help" ] || [ "$command" = "--help" ] || [ "$command" = "-h" ]; then
        show_help
        exit 0
    fi
    
    # 激活 Python 环境
    if [ "$command" != "status" ] && [ "$command" != "logs" ]; then
        activate_python_env
    fi
    
    # 执行命令
    case "$command" in
        start)
            case "$service" in
                web)
                    start_web
                    ;;
                celery)
                    start_celery
                    ;;
                beat)
                    start_beat
                    ;;
                all)
                    start_web
                    start_celery
                    start_beat
                    ;;
                *)
                    log_error "未知服务: $service"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
            
        stop)
            case "$service" in
                web)
                    stop_web
                    ;;
                celery)
                    stop_celery
                    ;;
                beat)
                    stop_beat
                    ;;
                all)
                    stop_beat
                    stop_celery
                    stop_web
                    ;;
                *)
                    log_error "未知服务: $service"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
            
        restart)
            case "$service" in
                web)
                    stop_web
                    start_web
                    ;;
                celery)
                    stop_celery
                    start_celery
                    ;;
                beat)
                    stop_beat
                    start_beat
                    ;;
                all)
                    stop_beat
                    stop_celery
                    stop_web
                    sleep 2
                    start_web
                    start_celery
                    start_beat
                    ;;
                *)
                    log_error "未知服务: $service"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
            
        status)
            echo ""
            echo "================================================================"
            echo "                    服务状态"
            echo "================================================================"
            echo ""
            
            case "$service" in
                web)
                    status_web
                    ;;
                celery)
                    status_celery
                    ;;
                beat)
                    status_beat
                    ;;
                all)
                    status_web
                    status_celery
                    status_beat
                    ;;
                *)
                    log_error "未知服务: $service"
                    show_help
                    exit 1
                    ;;
            esac
            
            echo ""
            echo "================================================================"
            echo ""
            ;;
            
        logs)
            case "$service" in
                web)
                    logs_web
                    ;;
                celery)
                    logs_celery
                    ;;
                beat)
                    logs_beat
                    ;;
                all)
                    logs_web
                    echo ""
                    logs_celery
                    echo ""
                    logs_beat
                    ;;
                *)
                    log_error "未知服务: $service"
                    show_help
                    exit 1
                    ;;
            esac
            ;;
            
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

