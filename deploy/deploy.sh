#!/bin/bash
# -*- coding: utf-8 -*-
#
# wrmVideo 一键部署脚本
#
# 功能：
# 1. 检查系统环境
# 2. 安装依赖软件
# 3. 创建 Python 环境
# 4. 配置数据库
# 5. 初始化项目
# 6. 启动服务
#
# 使用方法：
#   bash deploy.sh [选项]
#
# 选项：
#   --skip-check    跳过环境检查
#   --dev           开发环境部署
#   --prod          生产环境部署
#   --help          显示帮助信息

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_DIR="${PROJECT_ROOT}/deploy"

# 默认配置
SKIP_CHECK=false
ENV_TYPE="dev"  # dev 或 prod

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
wrmVideo 一键部署脚本

使用方法:
    bash deploy.sh [选项]

选项:
    --skip-check    跳过环境检查
    --dev           开发环境部署（默认）
    --prod          生产环境部署
    --help          显示此帮助信息

示例:
    # 开发环境部署
    bash deploy.sh --dev

    # 生产环境部署
    bash deploy.sh --prod

    # 跳过环境检查
    bash deploy.sh --skip-check

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-check)
                SKIP_CHECK=true
                shift
                ;;
            --dev)
                ENV_TYPE="dev"
                shift
                ;;
            --prod)
                ENV_TYPE="prod"
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

# 打印横幅
print_banner() {
    echo ""
    echo "================================================================"
    echo "                  wrmVideo 一键部署脚本"
    echo "================================================================"
    echo ""
    echo "部署类型: ${ENV_TYPE}"
    echo "项目目录: ${PROJECT_ROOT}"
    echo ""
    echo "================================================================"
    echo ""
}

# 检查系统环境
check_environment() {
    if [ "$SKIP_CHECK" = true ]; then
        log_warning "跳过环境检查"
        return 0
    fi

    log_info "开始环境检查..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python3，请先安装 Python 3.8+"
        exit 1
    fi
    
    # 运行环境检查脚本
    if [ -f "${DEPLOY_DIR}/check_environment.py" ]; then
        python3 "${DEPLOY_DIR}/check_environment.py"
        if [ $? -ne 0 ]; then
            log_error "环境检查失败，请查看报告并修复问题"
            exit 1
        fi
    else
        log_warning "未找到环境检查脚本，跳过详细检查"
    fi
    
    log_success "环境检查完成"
}

# 安装系统依赖
install_system_dependencies() {
    log_info "检查系统依赖..."
    
    OS_TYPE=$(uname -s)
    
    case "$OS_TYPE" in
        Darwin)
            log_info "检测到 macOS 系统"
            
            # 检查 Homebrew
            if ! command -v brew &> /dev/null; then
                log_warning "未安装 Homebrew，正在安装..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            # 安装 FFmpeg
            if ! command -v ffmpeg &> /dev/null; then
                log_info "安装 FFmpeg..."
                brew install ffmpeg
            fi
            
            # 安装 Redis
            if ! command -v redis-server &> /dev/null; then
                log_info "安装 Redis..."
                brew install redis
                brew services start redis
            fi
            
            # 安装 MySQL（可选）
            if [ "$ENV_TYPE" = "prod" ] && ! command -v mysql &> /dev/null; then
                log_info "安装 MySQL..."
                brew install mysql
                brew services start mysql
            fi
            ;;
            
        Linux)
            log_info "检测到 Linux 系统"
            
            # 检测发行版
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO=$ID
            else
                log_error "无法检测 Linux 发行版"
                exit 1
            fi
            
            case "$DISTRO" in
                ubuntu|debian)
                    log_info "检测到 Ubuntu/Debian 系统"
                    
                    sudo apt update
                    
                    # 安装 FFmpeg
                    if ! command -v ffmpeg &> /dev/null; then
                        log_info "安装 FFmpeg..."
                        sudo apt install -y ffmpeg
                    fi
                    
                    # 安装 Redis
                    if ! command -v redis-server &> /dev/null; then
                        log_info "安装 Redis..."
                        sudo apt install -y redis-server
                        sudo systemctl start redis
                        sudo systemctl enable redis
                    fi
                    
                    # 安装 MySQL（可选）
                    if [ "$ENV_TYPE" = "prod" ] && ! command -v mysql &> /dev/null; then
                        log_info "安装 MySQL..."
                        sudo apt install -y mysql-server
                        sudo systemctl start mysql
                        sudo systemctl enable mysql
                    fi
                    
                    # 安装开发工具
                    sudo apt install -y python3-dev libmysqlclient-dev build-essential
                    ;;
                    
                centos|rhel|fedora)
                    log_info "检测到 CentOS/RHEL/Fedora 系统"
                    
                    sudo yum install -y epel-release
                    
                    # 安装 FFmpeg
                    if ! command -v ffmpeg &> /dev/null; then
                        log_info "安装 FFmpeg..."
                        sudo yum install -y ffmpeg
                    fi
                    
                    # 安装 Redis
                    if ! command -v redis-server &> /dev/null; then
                        log_info "安装 Redis..."
                        sudo yum install -y redis
                        sudo systemctl start redis
                        sudo systemctl enable redis
                    fi
                    
                    # 安装 MySQL（可选）
                    if [ "$ENV_TYPE" = "prod" ] && ! command -v mysql &> /dev/null; then
                        log_info "安装 MySQL..."
                        sudo yum install -y mysql-server
                        sudo systemctl start mysqld
                        sudo systemctl enable mysqld
                    fi
                    
                    # 安装开发工具
                    sudo yum install -y python3-devel mysql-devel gcc
                    ;;
                    
                *)
                    log_warning "未知的 Linux 发行版: $DISTRO"
                    log_warning "请手动安装 FFmpeg、Redis 等依赖"
                    ;;
            esac
            ;;
            
        *)
            log_error "不支持的操作系统: $OS_TYPE"
            exit 1
            ;;
    esac
    
    log_success "系统依赖检查完成"
}

# 创建 Python 环境
setup_python_environment() {
    log_info "设置 Python 环境..."
    
    # 检查 Conda
    if command -v conda &> /dev/null; then
        log_info "使用 Conda 创建虚拟环境..."
        
        # 检查环境是否已存在
        if conda env list | grep -q "wrmvideo"; then
            log_warning "Conda 环境 'wrmvideo' 已存在"
            read -p "是否重新创建？(y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                conda env remove -n wrmvideo -y
                conda create -n wrmvideo python=3.10 -y
            fi
        else
            conda create -n wrmvideo python=3.10 -y
        fi
        
        # 激活环境并安装依赖
        log_info "安装 Python 依赖包..."
        eval "$(conda shell.bash hook)"
        conda activate wrmvideo
        pip install -r "${PROJECT_ROOT}/requirements.txt"
        
    else
        log_info "使用 venv 创建虚拟环境..."
        
        # 创建 venv
        if [ -d "${PROJECT_ROOT}/venv" ]; then
            log_warning "虚拟环境已存在"
            read -p "是否重新创建？(y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                rm -rf "${PROJECT_ROOT}/venv"
                python3 -m venv "${PROJECT_ROOT}/venv"
            fi
        else
            python3 -m venv "${PROJECT_ROOT}/venv"
        fi
        
        # 激活环境并安装依赖
        log_info "安装 Python 依赖包..."
        source "${PROJECT_ROOT}/venv/bin/activate"
        pip install --upgrade pip
        pip install -r "${PROJECT_ROOT}/requirements.txt"
    fi
    
    log_success "Python 环境设置完成"
}

# 配置项目
configure_project() {
    log_info "配置项目..."
    
    # 创建配置文件
    if [ ! -f "${PROJECT_ROOT}/config/config.py" ]; then
        log_info "创建配置文件..."
        cp "${PROJECT_ROOT}/config/config.example.py" "${PROJECT_ROOT}/config/config.py"
        log_warning "请编辑 config/config.py 填入 API 密钥"
        
        read -p "是否现在编辑配置文件？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vim} "${PROJECT_ROOT}/config/config.py"
        fi
    else
        log_info "配置文件已存在"
    fi
    
    # 创建必要目录
    log_info "创建项目目录..."
    mkdir -p "${PROJECT_ROOT}/data"
    mkdir -p "${PROJECT_ROOT}/Character_Images"
    mkdir -p "${PROJECT_ROOT}/async_tasks"
    mkdir -p "${PROJECT_ROOT}/done_tasks"
    mkdir -p "${PROJECT_ROOT}/logs"
    mkdir -p "${PROJECT_ROOT}/web/media"
    mkdir -p "${PROJECT_ROOT}/web/static"
    mkdir -p "${PROJECT_ROOT}/web/logs"
    
    # 设置权限
    chmod -R 755 "${PROJECT_ROOT}/data"
    chmod -R 755 "${PROJECT_ROOT}/logs"
    chmod -R 755 "${PROJECT_ROOT}/web/media"
    
    log_success "项目配置完成"
}

# 初始化数据库
initialize_database() {
    log_info "初始化数据库..."
    
    cd "${PROJECT_ROOT}/web"
    
    if [ "$ENV_TYPE" = "prod" ]; then
        # 生产环境使用 MySQL
        log_info "配置 MySQL 数据库..."
        
        read -p "请输入 MySQL root 密码: " -s MYSQL_ROOT_PASSWORD
        echo
        
        # 创建数据库
        mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "CREATE DATABASE IF NOT EXISTS wrm_video CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
            log_warning "数据库可能已存在或密码错误"
        }
        
        # 创建用户
        read -p "请输入数据库用户名 (默认: wrmvideo): " DB_USER
        DB_USER=${DB_USER:-wrmvideo}
        
        read -p "请输入数据库密码: " -s DB_PASSWORD
        echo
        
        mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';" 2>/dev/null || {
            log_warning "用户可能已存在"
        }
        
        mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "GRANT ALL PRIVILEGES ON wrm_video.* TO '${DB_USER}'@'localhost';" 2>/dev/null
        mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "FLUSH PRIVILEGES;" 2>/dev/null
        
        log_info "请更新 web/web/settings.py 中的数据库配置"
    else
        # 开发环境使用 SQLite
        log_info "使用 SQLite 数据库（开发环境）"
    fi
    
    # 执行数据库迁移
    log_info "执行数据库迁移..."
    python manage.py makemigrations
    python manage.py migrate
    
    # 创建超级管理员
    log_info "创建超级管理员..."
    python manage.py createsuperuser
    
    # 初始化权限系统
    log_info "初始化权限系统..."
    python manage.py setup_permissions
    
    # 添加管理员到管理员组
    if [ -f "${PROJECT_ROOT}/web/add_admin_to_group.py" ]; then
        python add_admin_to_group.py
    fi
    
    # 收集静态文件
    if [ "$ENV_TYPE" = "prod" ]; then
        log_info "收集静态文件..."
        python manage.py collectstatic --noinput
    fi
    
    cd "${PROJECT_ROOT}"
    
    log_success "数据库初始化完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    if [ "$ENV_TYPE" = "dev" ]; then
        # 开发环境
        log_info "开发环境模式"
        log_info "请在不同的终端窗口中运行以下命令："
        echo ""
        echo "  # 终端 1: 启动 Web 服务"
        echo "  cd ${PROJECT_ROOT}/web"
        echo "  python manage.py runserver 0.0.0.0:8000"
        echo ""
        echo "  # 终端 2: 启动 Celery Worker"
        echo "  cd ${PROJECT_ROOT}/web"
        echo "  celery -A web worker --loglevel=info"
        echo ""
        echo "  # 终端 3: 启动 Celery Beat"
        echo "  cd ${PROJECT_ROOT}/web"
        echo "  celery -A web beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
        echo ""
        
    else
        # 生产环境
        log_info "生产环境模式"
        
        if [ -f "${DEPLOY_DIR}/service_manager.sh" ]; then
            bash "${DEPLOY_DIR}/service_manager.sh" start
        else
            log_warning "未找到服务管理脚本"
            log_info "请手动启动服务或配置 systemd"
        fi
    fi
    
    log_success "服务启动完成"
}

# 打印完成信息
print_completion() {
    echo ""
    echo "================================================================"
    echo "                    部署完成！"
    echo "================================================================"
    echo ""
    
    if [ "$ENV_TYPE" = "dev" ]; then
        echo "开发环境已配置完成"
        echo ""
        echo "访问地址:"
        echo "  - Web 管理界面: http://127.0.0.1:8000/video/dashboard/"
        echo "  - Admin 后台: http://127.0.0.1:8000/admin/"
        echo ""
        echo "下一步:"
        echo "  1. 在不同终端中启动服务（见上方说明）"
        echo "  2. 访问 Web 界面开始使用"
        echo ""
    else
        echo "生产环境已配置完成"
        echo ""
        echo "访问地址:"
        echo "  - Web 管理界面: http://your_domain.com/video/dashboard/"
        echo "  - Admin 后台: http://your_domain.com/admin/"
        echo ""
        echo "下一步:"
        echo "  1. 配置 Nginx 反向代理"
        echo "  2. 配置 SSL 证书"
        echo "  3. 配置 systemd 服务"
        echo "  4. 设置定期备份"
        echo ""
    fi
    
    echo "文档:"
    echo "  - 部署文档: ${DEPLOY_DIR}/DEPLOYMENT.md"
    echo "  - 使用指南: ${PROJECT_ROOT}/README.md"
    echo "  - 环境检查报告: ${DEPLOY_DIR}/environment_check_report.txt"
    echo ""
    echo "================================================================"
    echo ""
}

# 主函数
main() {
    parse_args "$@"
    print_banner
    
    # 执行部署步骤
    check_environment
    install_system_dependencies
    setup_python_environment
    configure_project
    initialize_database
    start_services
    
    print_completion
}

# 运行主函数
main "$@"

