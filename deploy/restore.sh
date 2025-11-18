#!/bin/bash
# -*- coding: utf-8 -*-
#
# wrmVideo 恢复脚本
#
# 功能：
# 1. 恢复数据库
# 2. 恢复配置文件
# 3. 恢复数据目录
# 4. 恢复角色图片
# 5. 验证恢复结果
#
# 使用方法：
#   bash restore.sh <备份目录> [选项]
#
# 选项：
#   --db-only       仅恢复数据库
#   --config-only   仅恢复配置
#   --data-only     仅恢复数据
#   --force         强制覆盖现有文件
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
BACKUP_PATH=""
RESTORE_TYPE="full"
FORCE=false

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
wrmVideo 恢复脚本

使用方法:
    bash restore.sh <备份目录> [选项]

选项:
    --db-only       仅恢复数据库
    --config-only   仅恢复配置
    --data-only     仅恢复数据
    --force         强制覆盖现有文件
    --help          显示帮助信息

示例:
    # 完整恢复
    bash restore.sh /path/to/backup_20250118_120000

    # 仅恢复数据库
    bash restore.sh /path/to/backup_20250118_120000 --db-only

    # 强制覆盖
    bash restore.sh /path/to/backup_20250118_120000 --force

恢复内容:
    - 数据库（MySQL/SQLite）
    - 配置文件（config/）
    - 数据目录（data/）
    - 角色图片（Character_Images/）
    - Web 媒体文件（web/media/）

警告:
    恢复操作会覆盖现有文件，请确保已做好备份！

EOF
}

# 解析命令行参数
parse_args() {
    if [ $# -eq 0 ]; then
        log_error "请指定备份目录"
        show_help
        exit 1
    fi
    
    BACKUP_PATH="$1"
    shift
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --db-only)
                RESTORE_TYPE="db"
                shift
                ;;
            --config-only)
                RESTORE_TYPE="config"
                shift
                ;;
            --data-only)
                RESTORE_TYPE="data"
                shift
                ;;
            --force)
                FORCE=true
                shift
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

# 验证备份目录
validate_backup() {
    log_info "验证备份目录..."
    
    if [ ! -d "$BACKUP_PATH" ]; then
        log_error "备份目录不存在: $BACKUP_PATH"
        exit 1
    fi
    
    if [ ! -f "${BACKUP_PATH}/MANIFEST.txt" ]; then
        log_warning "未找到备份清单文件"
    else
        log_info "备份清单:"
        cat "${BACKUP_PATH}/MANIFEST.txt"
        echo ""
    fi
    
    log_success "备份目录验证通过"
}

# 确认恢复操作
confirm_restore() {
    if [ "$FORCE" = false ]; then
        log_warning "恢复操作会覆盖现有文件！"
        read -p "是否继续？(yes/no): " -r
        echo
        
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "操作已取消"
            exit 0
        fi
    fi
}

# 恢复数据库
restore_database() {
    log_info "恢复数据库..."
    
    # SQLite 数据库
    if [ -f "${BACKUP_PATH}/db.sqlite3" ]; then
        log_info "恢复 SQLite 数据库..."
        
        # 备份现有数据库
        if [ -f "${PROJECT_ROOT}/web/db.sqlite3" ]; then
            mv "${PROJECT_ROOT}/web/db.sqlite3" "${PROJECT_ROOT}/web/db.sqlite3.bak.$(date +%Y%m%d_%H%M%S)"
            log_info "已备份现有数据库"
        fi
        
        cp "${BACKUP_PATH}/db.sqlite3" "${PROJECT_ROOT}/web/db.sqlite3"
        log_success "SQLite 数据库恢复完成"
        
    # MySQL 数据库
    elif [ -f "${BACKUP_PATH}/database.sql.gz" ] || [ -f "${BACKUP_PATH}/database.sql" ]; then
        log_info "恢复 MySQL 数据库..."
        
        DB_NAME="wrm_video"
        DB_USER="wrmvideo"
        
        read -p "请输入数据库密码: " -s DB_PASSWORD
        echo
        
        # 解压 SQL 文件（如果是压缩的）
        if [ -f "${BACKUP_PATH}/database.sql.gz" ]; then
            gunzip -c "${BACKUP_PATH}/database.sql.gz" > /tmp/restore_db.sql
            SQL_FILE="/tmp/restore_db.sql"
        else
            SQL_FILE="${BACKUP_PATH}/database.sql"
        fi
        
        # 恢复数据库
        mysql -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SQL_FILE" 2>/dev/null || {
            log_error "数据库恢复失败"
            rm -f /tmp/restore_db.sql
            return 1
        }
        
        # 清理临时文件
        rm -f /tmp/restore_db.sql
        
        log_success "MySQL 数据库恢复完成"
    else
        log_warning "未找到数据库备份文件"
    fi
}

# 恢复配置文件
restore_config() {
    log_info "恢复配置文件..."
    
    if [ -f "${BACKUP_PATH}/config.tar.gz" ]; then
        # 备份现有配置
        if [ -d "${PROJECT_ROOT}/config" ]; then
            mv "${PROJECT_ROOT}/config" "${PROJECT_ROOT}/config.bak.$(date +%Y%m%d_%H%M%S)"
            log_info "已备份现有配置"
        fi
        
        tar -xzf "${BACKUP_PATH}/config.tar.gz" -C "${PROJECT_ROOT}"
        log_success "配置文件恢复完成"
    else
        log_warning "未找到配置文件备份"
    fi
}

# 恢复数据目录
restore_data() {
    log_info "恢复数据目录..."
    
    if [ -f "${BACKUP_PATH}/data.tar.gz" ]; then
        # 备份现有数据
        if [ -d "${PROJECT_ROOT}/data" ]; then
            log_warning "数据目录已存在"
            
            if [ "$FORCE" = false ]; then
                read -p "是否覆盖现有数据？(yes/no): " -r
                echo
                
                if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                    log_info "跳过数据目录恢复"
                    return 0
                fi
            fi
            
            mv "${PROJECT_ROOT}/data" "${PROJECT_ROOT}/data.bak.$(date +%Y%m%d_%H%M%S)"
            log_info "已备份现有数据"
        fi
        
        tar -xzf "${BACKUP_PATH}/data.tar.gz" -C "${PROJECT_ROOT}"
        log_success "数据目录恢复完成"
    else
        log_warning "未找到数据目录备份"
    fi
}

# 恢复角色图片
restore_character_images() {
    log_info "恢复角色图片..."
    
    if [ -f "${BACKUP_PATH}/character_images.tar.gz" ]; then
        # 备份现有图片
        if [ -d "${PROJECT_ROOT}/Character_Images" ]; then
            log_warning "角色图片目录已存在"
            
            if [ "$FORCE" = false ]; then
                read -p "是否覆盖现有图片？(yes/no): " -r
                echo
                
                if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                    log_info "跳过角色图片恢复"
                    return 0
                fi
            fi
            
            mv "${PROJECT_ROOT}/Character_Images" "${PROJECT_ROOT}/Character_Images.bak.$(date +%Y%m%d_%H%M%S)"
            log_info "已备份现有图片"
        fi
        
        tar -xzf "${BACKUP_PATH}/character_images.tar.gz" -C "${PROJECT_ROOT}"
        log_success "角色图片恢复完成"
    else
        log_warning "未找到角色图片备份"
    fi
}

# 恢复 Web 媒体文件
restore_media() {
    log_info "恢复 Web 媒体文件..."
    
    if [ -f "${BACKUP_PATH}/media.tar.gz" ]; then
        # 备份现有媒体文件
        if [ -d "${PROJECT_ROOT}/web/media" ]; then
            mv "${PROJECT_ROOT}/web/media" "${PROJECT_ROOT}/web/media.bak.$(date +%Y%m%d_%H%M%S)"
            log_info "已备份现有媒体文件"
        fi
        
        mkdir -p "${PROJECT_ROOT}/web"
        tar -xzf "${BACKUP_PATH}/media.tar.gz" -C "${PROJECT_ROOT}/web"
        log_success "媒体文件恢复完成"
    else
        log_warning "未找到媒体文件备份"
    fi
}

# 验证恢复结果
verify_restore() {
    log_info "验证恢复结果..."
    
    local errors=0
    
    # 检查数据库
    if [ -f "${PROJECT_ROOT}/web/db.sqlite3" ]; then
        log_success "✓ SQLite 数据库存在"
    elif command -v mysql &> /dev/null; then
        log_success "✓ MySQL 数据库（需手动验证）"
    else
        log_warning "⚠ 未找到数据库"
        ((errors++))
    fi
    
    # 检查配置文件
    if [ -f "${PROJECT_ROOT}/config/config.py" ]; then
        log_success "✓ 配置文件存在"
    else
        log_warning "⚠ 配置文件不存在"
        ((errors++))
    fi
    
    # 检查数据目录
    if [ -d "${PROJECT_ROOT}/data" ]; then
        log_success "✓ 数据目录存在"
    else
        log_warning "⚠ 数据目录不存在"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        log_success "恢复验证通过"
    else
        log_warning "发现 $errors 个问题"
    fi
}

# 打印恢复摘要
print_summary() {
    echo ""
    echo "================================================================"
    echo "                    恢复完成"
    echo "================================================================"
    echo ""
    echo "恢复类型: $RESTORE_TYPE"
    echo "备份路径: $BACKUP_PATH"
    echo ""
    echo "下一步:"
    echo "  1. 验证数据库连接"
    echo "  2. 检查配置文件"
    echo "  3. 重启服务"
    echo "  4. 测试功能"
    echo ""
    echo "重启服务命令:"
    echo "  bash deploy/service_manager.sh restart"
    echo ""
    echo "================================================================"
    echo ""
}

# 主函数
main() {
    parse_args "$@"
    
    echo ""
    echo "================================================================"
    echo "                  wrmVideo 恢复工具"
    echo "================================================================"
    echo ""
    
    validate_backup
    confirm_restore
    
    case "$RESTORE_TYPE" in
        full)
            restore_database
            restore_config
            restore_data
            restore_character_images
            restore_media
            ;;
        db)
            restore_database
            ;;
        config)
            restore_config
            ;;
        data)
            restore_data
            restore_character_images
            restore_media
            ;;
        *)
            log_error "未知恢复类型: $RESTORE_TYPE"
            exit 1
            ;;
    esac
    
    verify_restore
    print_summary
}

# 运行主函数
main "$@"

