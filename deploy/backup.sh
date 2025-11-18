#!/bin/bash
# -*- coding: utf-8 -*-
#
# wrmVideo 备份脚本
#
# 功能：
# 1. 备份数据库
# 2. 备份配置文件
# 3. 备份数据目录
# 4. 备份角色图片
# 5. 创建备份清单
#
# 使用方法：
#   bash backup.sh [选项]
#
# 选项：
#   --full          完整备份（默认）
#   --db-only       仅备份数据库
#   --config-only   仅备份配置
#   --data-only     仅备份数据
#   --output DIR    指定备份输出目录
#   --help          显示帮助信息

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目配置
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 备份选项
BACKUP_TYPE="full"
OUTPUT_DIR=""

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

# 显示帮助信息
show_help() {
    cat << EOF
wrmVideo 备份脚本

使用方法:
    bash backup.sh [选项]

选项:
    --full          完整备份（默认）
    --db-only       仅备份数据库
    --config-only   仅备份配置
    --data-only     仅备份数据
    --output DIR    指定备份输出目录
    --help          显示帮助信息

示例:
    # 完整备份
    bash backup.sh

    # 仅备份数据库
    bash backup.sh --db-only

    # 指定输出目录
    bash backup.sh --output /path/to/backup

备份内容:
    - 数据库（MySQL/SQLite）
    - 配置文件（config/）
    - 数据目录（data/）
    - 角色图片（Character_Images/）
    - Web 媒体文件（web/media/）

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --full)
                BACKUP_TYPE="full"
                shift
                ;;
            --db-only)
                BACKUP_TYPE="db"
                shift
                ;;
            --config-only)
                BACKUP_TYPE="config"
                shift
                ;;
            --data-only)
                BACKUP_TYPE="data"
                shift
                ;;
            --output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 初始化备份目录
init_backup_dir() {
    if [ -n "$OUTPUT_DIR" ]; then
        BACKUP_DIR="$OUTPUT_DIR"
    fi
    
    mkdir -p "$BACKUP_DIR"
    
    # 创建本次备份目录
    BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"
    mkdir -p "$BACKUP_PATH"
    
    log_info "备份目录: $BACKUP_PATH"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    # 检查数据库类型
    if [ -f "${PROJECT_ROOT}/web/db.sqlite3" ]; then
        # SQLite 数据库
        log_info "检测到 SQLite 数据库"
        
        cp "${PROJECT_ROOT}/web/db.sqlite3" "${BACKUP_PATH}/db.sqlite3"
        log_success "SQLite 数据库备份完成"
        
    elif command -v mysql &> /dev/null; then
        # MySQL 数据库
        log_info "检测到 MySQL 数据库"
        
        # 从配置文件读取数据库信息
        DB_NAME="wrm_video"
        DB_USER="wrmvideo"
        
        read -p "请输入数据库密码: " -s DB_PASSWORD
        echo
        
        mysqldump -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "${BACKUP_PATH}/database.sql" 2>/dev/null || {
            log_error "数据库备份失败"
            return 1
        }
        
        # 压缩 SQL 文件
        gzip "${BACKUP_PATH}/database.sql"
        
        log_success "MySQL 数据库备份完成"
    else
        log_warning "未找到数据库"
    fi
}

# 备份配置文件
backup_config() {
    log_info "备份配置文件..."
    
    if [ -d "${PROJECT_ROOT}/config" ]; then
        tar -czf "${BACKUP_PATH}/config.tar.gz" -C "${PROJECT_ROOT}" config/
        log_success "配置文件备份完成"
    else
        log_warning "配置目录不存在"
    fi
}

# 备份数据目录
backup_data() {
    log_info "备份数据目录..."
    
    if [ -d "${PROJECT_ROOT}/data" ]; then
        # 计算数据目录大小
        DATA_SIZE=$(du -sh "${PROJECT_ROOT}/data" | cut -f1)
        log_info "数据目录大小: $DATA_SIZE"
        
        # 备份数据目录（排除临时文件）
        tar -czf "${BACKUP_PATH}/data.tar.gz" \
            -C "${PROJECT_ROOT}" \
            --exclude='*.tmp' \
            --exclude='*.log' \
            --exclude='__pycache__' \
            data/
        
        log_success "数据目录备份完成"
    else
        log_warning "数据目录不存在"
    fi
}

# 备份角色图片
backup_character_images() {
    log_info "备份角色图片..."
    
    if [ -d "${PROJECT_ROOT}/Character_Images" ]; then
        # 计算图片目录大小
        IMAGE_SIZE=$(du -sh "${PROJECT_ROOT}/Character_Images" | cut -f1)
        log_info "角色图片大小: $IMAGE_SIZE"
        
        tar -czf "${BACKUP_PATH}/character_images.tar.gz" \
            -C "${PROJECT_ROOT}" \
            Character_Images/
        
        log_success "角色图片备份完成"
    else
        log_warning "角色图片目录不存在"
    fi
}

# 备份 Web 媒体文件
backup_media() {
    log_info "备份 Web 媒体文件..."
    
    if [ -d "${PROJECT_ROOT}/web/media" ]; then
        MEDIA_SIZE=$(du -sh "${PROJECT_ROOT}/web/media" | cut -f1)
        log_info "媒体文件大小: $MEDIA_SIZE"
        
        tar -czf "${BACKUP_PATH}/media.tar.gz" \
            -C "${PROJECT_ROOT}/web" \
            media/
        
        log_success "媒体文件备份完成"
    else
        log_warning "媒体文件目录不存在"
    fi
}

# 创建备份清单
create_manifest() {
    log_info "创建备份清单..."
    
    MANIFEST="${BACKUP_PATH}/MANIFEST.txt"
    
    cat > "$MANIFEST" << EOF
wrmVideo 备份清单
================

备份时间: $(date '+%Y-%m-%d %H:%M:%S')
备份类型: $BACKUP_TYPE
备份路径: $BACKUP_PATH

备份内容:
--------
EOF
    
    # 列出备份文件
    for file in "${BACKUP_PATH}"/*; do
        if [ -f "$file" ] && [ "$file" != "$MANIFEST" ]; then
            filename=$(basename "$file")
            filesize=$(du -h "$file" | cut -f1)
            echo "  - $filename ($filesize)" >> "$MANIFEST"
        fi
    done
    
    # 添加系统信息
    cat >> "$MANIFEST" << EOF

系统信息:
--------
  操作系统: $(uname -s)
  主机名: $(hostname)
  Python 版本: $(python3 --version 2>&1)
  
项目信息:
--------
  项目路径: $PROJECT_ROOT
  Git 分支: $(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo "N/A")
  Git 提交: $(cd "$PROJECT_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo "N/A")

EOF
    
    log_success "备份清单创建完成"
}

# 计算备份大小
calculate_backup_size() {
    TOTAL_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    log_info "备份总大小: $TOTAL_SIZE"
}

# 清理旧备份
cleanup_old_backups() {
    log_info "清理旧备份..."
    
    # 保留最近 30 天的备份
    find "$BACKUP_DIR" -name "backup_*" -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null || true
    
    # 统计备份数量
    BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_*" -type d | wc -l)
    log_info "当前备份数量: $BACKUP_COUNT"
}

# 打印备份摘要
print_summary() {
    echo ""
    echo "================================================================"
    echo "                    备份完成"
    echo "================================================================"
    echo ""
    echo "备份类型: $BACKUP_TYPE"
    echo "备份路径: $BACKUP_PATH"
    echo "备份大小: $TOTAL_SIZE"
    echo ""
    echo "备份文件:"
    ls -lh "$BACKUP_PATH" | tail -n +2 | awk '{printf "  - %-30s %10s\n", $9, $5}'
    echo ""
    echo "================================================================"
    echo ""
}

# 主函数
main() {
    parse_args "$@"
    
    echo ""
    echo "================================================================"
    echo "                  wrmVideo 备份工具"
    echo "================================================================"
    echo ""
    
    init_backup_dir
    
    case "$BACKUP_TYPE" in
        full)
            backup_database
            backup_config
            backup_data
            backup_character_images
            backup_media
            ;;
        db)
            backup_database
            ;;
        config)
            backup_config
            ;;
        data)
            backup_data
            backup_character_images
            backup_media
            ;;
        *)
            log_error "未知备份类型: $BACKUP_TYPE"
            exit 1
            ;;
    esac
    
    create_manifest
    calculate_backup_size
    cleanup_old_backups
    print_summary
}

# 运行主函数
main "$@"

