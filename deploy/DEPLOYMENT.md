# 🚀 wrmVideo 部署文档

本文档提供完整的项目部署指南，包括开发环境和生产环境的部署方案。

## 📋 目录

- [环境要求](#环境要求)
- [快速部署](#快速部署)
- [详细部署步骤](#详细部署步骤)
- [配置说明](#配置说明)
- [服务管理](#服务管理)
- [备份与恢复](#备份与恢复)
- [故障排查](#故障排查)
- [性能优化](#性能优化)

## 🔧 环境要求

### 系统要求

- **操作系统**: macOS 10.15+ / Ubuntu 20.04+ / CentOS 8+
- **Python**: 3.8 或更高版本
- **内存**: 最低 8GB，推荐 16GB+
- **存储**: 最低 50GB 可用空间
- **网络**: 稳定的互联网连接

### 软件依赖

#### 必需软件

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **FFmpeg**（支持 NVENC 编码器）
   ```bash
   ffmpeg -version
   ```

3. **MySQL 5.7+** 或 **SQLite**（开发环境）
   ```bash
   mysql --version
   ```

4. **Redis 6.0+**（用于 Celery 任务队列）
   ```bash
   redis-server --version
   ```

5. **Conda**（推荐用于环境管理）
   ```bash
   conda --version
   ```

#### 可选软件（用于 GPU 加速）

- **NVIDIA GPU 驱动** (版本 >= 470.x)
- **CUDA Toolkit** (版本 >= 11.0)
- **cuDNN** (版本 >= 8.0)

### API 服务

需要以下 API 服务的访问权限：

1. **火山引擎 TTS**：语音合成服务
2. **豆包大模型**：文案生成和图片分析
3. **火山引擎图像生成**：图片生成服务
4. **火山引擎 TOS**：对象存储服务
5. **ComfyUI API**（可选）：高质量图片生成

## ⚡ 快速部署

### 方式一：使用一键部署脚本（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd wrmVideo

# 2. 运行一键部署脚本
bash deploy/deploy.sh

# 3. 按照提示完成配置
```

### 方式二：使用 Docker 部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

## 📝 详细部署步骤

### 步骤 1：环境准备

#### 1.1 安装系统依赖

**macOS:**
```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 FFmpeg
brew install ffmpeg

# 安装 MySQL（可选）
brew install mysql
brew services start mysql

# 安装 Redis
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
# 更新包列表
sudo apt update

# 安装 FFmpeg
sudo apt install -y ffmpeg

# 安装 MySQL
sudo apt install -y mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql

# 安装 Redis
sudo apt install -y redis-server
sudo systemctl start redis
sudo systemctl enable redis

# 安装其他依赖
sudo apt install -y python3-dev libmysqlclient-dev build-essential
```

**CentOS/RHEL:**
```bash
# 安装 EPEL 仓库
sudo yum install -y epel-release

# 安装 FFmpeg
sudo yum install -y ffmpeg

# 安装 MySQL
sudo yum install -y mysql-server
sudo systemctl start mysqld
sudo systemctl enable mysqld

# 安装 Redis
sudo yum install -y redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### 1.2 安装 Conda（推荐）

```bash
# 下载 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# 安装
bash Miniconda3-latest-Linux-x86_64.sh

# 重新加载 shell
source ~/.bashrc
```

#### 1.3 检查环境

```bash
# 运行环境检查脚本
python deploy/check_environment.py

# 查看检查报告
cat deploy/environment_check_report.txt
```

### 步骤 2：创建 Python 环境

```bash
# 创建 Conda 环境
conda create -n wrmvideo python=3.10 -y

# 激活环境
conda activate wrmvideo

# 安装 Python 依赖
pip install -r requirements.txt

# 验证安装
python -c "import django; print(django.get_version())"
```

### 步骤 3：配置项目

#### 3.1 创建配置文件

```bash
# 复制配置模板
cp config/config.example.py config/config.py

# 编辑配置文件
vim config/config.py
```

#### 3.2 配置 API 密钥

编辑 `config/config.py`，填入以下信息：

```python
# TTS 语音合成配置
TTS_CONFIG = {
    "appid": "your_appid_here",
    "access_token": "your_access_token",
    "cluster": "volcano_tts",
    "voice_type": "BV701_streaming",
    "host": "openspeech.bytedance.com"
}

# 豆包大模型配置
ARK_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "your_api_key_here",
    "model": "doubao-seed-1.6-250615"
}

# 图片生成配置
IMAGE_TWO_CONFIG = {
    "access_key": "your_access_key",
    "secret_key": "your_secret_key",
    "req_key": "high_aes_general_v21_L",
    "default_width": 780,
    "default_height": 1280,
    "scale": 3.5,
    "ddim_steps": 25,
    "use_pre_llm": True,
    "use_sr": True,
    "return_url": False
}

# ComfyUI 配置（可选）
COMFYUI_CONFIG = {
    "default_host": "127.0.0.1:8188",
    "timeout": 300,
    "poll_interval": 1.0
}
```

#### 3.3 配置数据库

**使用 MySQL（生产环境推荐）:**

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE wrm_video CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 创建用户并授权
mysql -u root -p -e "CREATE USER 'wrmvideo'@'localhost' IDENTIFIED BY 'your_password';"
mysql -u root -p -e "GRANT ALL PRIVILEGES ON wrm_video.* TO 'wrmvideo'@'localhost';"
mysql -u root -p -e "FLUSH PRIVILEGES;"
```

编辑 `web/web/settings.py`：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wrm_video',
        'USER': 'wrmvideo',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}
```

**使用 SQLite（开发环境）:**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

#### 3.4 配置 Redis

编辑 `web/web/settings.py`：

```python
# Celery 配置
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Django 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 步骤 4：初始化数据库

```bash
# 进入 web 目录
cd web

# 执行数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级管理员
python manage.py createsuperuser

# 初始化权限系统
python manage.py setup_permissions

# 将 admin 用户添加到管理员组
python add_admin_to_group.py

# 验证配置
python check_admin_user.py
```

### 步骤 5：创建必要目录

```bash
# 回到项目根目录
cd ..

# 创建数据目录
mkdir -p data
mkdir -p Character_Images
mkdir -p async_tasks
mkdir -p done_tasks
mkdir -p logs

# 创建 Web 相关目录
mkdir -p web/media
mkdir -p web/static
mkdir -p web/logs

# 设置权限
chmod -R 755 data
chmod -R 755 web/media
chmod -R 755 logs
```

### 步骤 6：收集静态文件

```bash
cd web
python manage.py collectstatic --noinput
```

### 步骤 7：启动服务

#### 7.1 启动 Web 服务

**开发环境:**
```bash
cd web
python manage.py runserver 0.0.0.0:8000
```

**生产环境（使用 Gunicorn）:**
```bash
cd web
gunicorn web.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 300 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --daemon
```

#### 7.2 启动 Celery Worker

```bash
cd web
celery -A web worker --loglevel=info --concurrency=4 --logfile=logs/celery_worker.log &
```

#### 7.3 启动 Celery Beat（定时任务）

```bash
cd web
celery -A web beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=logs/celery_beat.log &
```

#### 7.4 使用服务管理脚本

```bash
# 启动所有服务
bash deploy/service_manager.sh start

# 停止所有服务
bash deploy/service_manager.sh stop

# 重启所有服务
bash deploy/service_manager.sh restart

# 查看服务状态
bash deploy/service_manager.sh status
```

### 步骤 8：配置 Nginx（生产环境）

创建 Nginx 配置文件 `/etc/nginx/sites-available/wrmvideo`：

```nginx
upstream wrmvideo_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your_domain.com;
    
    client_max_body_size 500M;
    
    location /static/ {
        alias /path/to/wrmVideo/web/static/;
    }
    
    location /media/ {
        alias /path/to/wrmVideo/web/media/;
    }
    
    location / {
        proxy_pass http://wrmvideo_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/wrmvideo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 步骤 9：配置 Systemd 服务（生产环境）

创建服务文件：

**Web 服务** (`/etc/systemd/system/wrmvideo-web.service`):
```ini
[Unit]
Description=wrmVideo Web Service
After=network.target mysql.service redis.service

[Service]
Type=notify
User=your_user
Group=your_group
WorkingDirectory=/path/to/wrmVideo/web
Environment="PATH=/path/to/conda/envs/wrmvideo/bin"
ExecStart=/path/to/conda/envs/wrmvideo/bin/gunicorn web.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 300 \
    --access-logfile /path/to/wrmVideo/logs/gunicorn_access.log \
    --error-logfile /path/to/wrmVideo/logs/gunicorn_error.log
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Worker** (`/etc/systemd/system/wrmvideo-celery.service`):
```ini
[Unit]
Description=wrmVideo Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=your_user
Group=your_group
WorkingDirectory=/path/to/wrmVideo/web
Environment="PATH=/path/to/conda/envs/wrmvideo/bin"
ExecStart=/path/to/conda/envs/wrmvideo/bin/celery -A web worker \
    --loglevel=info \
    --concurrency=4 \
    --logfile=/path/to/wrmVideo/logs/celery_worker.log \
    --pidfile=/var/run/celery/worker.pid
Restart=always

[Install]
WantedBy=multi-user.target
```

**Celery Beat** (`/etc/systemd/system/wrmvideo-celerybeat.service`):
```ini
[Unit]
Description=wrmVideo Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=your_user
Group=your_group
WorkingDirectory=/path/to/wrmVideo/web
Environment="PATH=/path/to/conda/envs/wrmvideo/bin"
ExecStart=/path/to/conda/envs/wrmvideo/bin/celery -A web beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --logfile=/path/to/wrmVideo/logs/celery_beat.log
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable wrmvideo-web wrmvideo-celery wrmvideo-celerybeat
sudo systemctl start wrmvideo-web wrmvideo-celery wrmvideo-celerybeat
sudo systemctl status wrmvideo-web wrmvideo-celery wrmvideo-celerybeat
```

## 🔐 安全配置

### 1. 设置 Django SECRET_KEY

```bash
# 生成新的 SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

将生成的密钥添加到 `web/web/settings.py`：

```python
SECRET_KEY = 'your_generated_secret_key_here'
```

### 2. 配置 ALLOWED_HOSTS

编辑 `web/web/settings.py`：

```python
ALLOWED_HOSTS = ['your_domain.com', 'www.your_domain.com', 'localhost', '127.0.0.1']
```

### 3. 关闭 DEBUG 模式（生产环境）

```python
DEBUG = False
```

### 4. 配置 HTTPS（推荐）

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

### 5. 设置文件权限

```bash
# 设置项目目录权限
chmod -R 755 /path/to/wrmVideo
chmod -R 700 /path/to/wrmVideo/config
chmod 600 /path/to/wrmVideo/config/config.py

# 设置日志目录权限
chmod -R 755 /path/to/wrmVideo/logs
chown -R your_user:your_group /path/to/wrmVideo/logs
```

## 📊 监控与日志

### 日志位置

- **Web 访问日志**: `logs/gunicorn_access.log`
- **Web 错误日志**: `logs/gunicorn_error.log`
- **Celery Worker 日志**: `logs/celery_worker.log`
- **Celery Beat 日志**: `logs/celery_beat.log`
- **图片生成日志**: `logs/gen_image_async_v*.log`

### 查看日志

```bash
# 实时查看 Web 日志
tail -f logs/gunicorn_access.log

# 实时查看 Celery 日志
tail -f logs/celery_worker.log

# 查看最近 100 行错误日志
tail -n 100 logs/gunicorn_error.log

# 使用日志监控脚本
python web/watch_celery_logs.py
```

### 日志轮转

创建 logrotate 配置 `/etc/logrotate.d/wrmvideo`：

```
/path/to/wrmVideo/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 your_user your_group
    sharedscripts
    postrotate
        systemctl reload wrmvideo-web
        systemctl reload wrmvideo-celery
    endscript
}
```

## 🔄 备份与恢复

### 备份

```bash
# 使用备份脚本
bash deploy/backup.sh

# 手动备份数据库
mysqldump -u wrmvideo -p wrm_video > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz config/

# 备份数据目录
tar -czf data_backup_$(date +%Y%m%d_%H%M%S).tar.gz data/
```

### 恢复

```bash
# 恢复数据库
mysql -u wrmvideo -p wrm_video < backup_20250118_120000.sql

# 恢复配置文件
tar -xzf config_backup_20250118_120000.tar.gz

# 恢复数据目录
tar -xzf data_backup_20250118_120000.tar.gz
```

### 自动备份

添加到 crontab：

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点自动备份
0 2 * * * /path/to/wrmVideo/deploy/backup.sh
```

## 🚨 故障排查

### 常见问题

#### 1. Web 服务无法启动

```bash
# 检查端口占用
sudo lsof -i :8000

# 检查日志
tail -f logs/gunicorn_error.log

# 检查数据库连接
python web/manage.py dbshell
```

#### 2. Celery 任务不执行

```bash
# 检查 Redis 连接
redis-cli ping

# 检查 Celery Worker 状态
celery -A web inspect active

# 重启 Celery
bash deploy/service_manager.sh restart celery
```

#### 3. 图片生成失败

```bash
# 检查 API 配置
python -c "from config.config import IMAGE_TWO_CONFIG; print(IMAGE_TWO_CONFIG)"

# 检查异步任务
python check_async_tasks.py --check-once

# 查看生成日志
tail -f logs/gen_image_async_v4.log
```

#### 4. FFmpeg 编码错误

```bash
# 检查 FFmpeg 版本
ffmpeg -version

# 检查 NVENC 支持
ffmpeg -encoders | grep nvenc

# 测试编码
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 -c:v h264_nvenc -f null -
```

#### 5. 数据库连接失败

```bash
# 检查 MySQL 服务
sudo systemctl status mysql

# 测试连接
mysql -u wrmvideo -p -e "SELECT 1;"

# 检查权限
mysql -u root -p -e "SHOW GRANTS FOR 'wrmvideo'@'localhost';"
```

### 性能优化

#### 1. 数据库优化

```sql
-- 添加索引
ALTER TABLE video_chapter ADD INDEX idx_review_status (review_status);
ALTER TABLE video_chapter ADD INDEX idx_novel_id (novel_id);

-- 优化查询
ANALYZE TABLE video_chapter;
OPTIMIZE TABLE video_chapter;
```

#### 2. Redis 优化

编辑 `/etc/redis/redis.conf`：

```conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

#### 3. Celery 优化

```python
# web/web/celery.py
app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=3600,
    task_soft_time_limit=3000,
)
```

#### 4. Nginx 优化

```nginx
# 启用 gzip 压缩
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# 启用缓存
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## 🔧 维护任务

### 定期维护

```bash
# 每周执行
# 1. 清理过期日志
find logs/ -name "*.log" -mtime +30 -delete

# 2. 清理临时文件
find async_tasks/ -name "*.txt" -mtime +7 -delete

# 3. 优化数据库
mysql -u wrmvideo -p wrm_video -e "OPTIMIZE TABLE video_chapter, video_novel;"

# 4. 清理 Redis
redis-cli FLUSHDB

# 5. 检查磁盘空间
df -h
```

### 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新依赖
conda activate wrmvideo
pip install -r requirements.txt --upgrade

# 3. 执行数据库迁移
cd web
python manage.py migrate

# 4. 收集静态文件
python manage.py collectstatic --noinput

# 5. 重启服务
cd ..
bash deploy/service_manager.sh restart
```

## 📞 技术支持

如遇到问题，请：

1. 查看日志文件
2. 运行环境检查脚本：`python deploy/check_environment.py`
3. 查看故障排查章节
4. 联系技术支持团队

## 📚 相关文档

- [README.md](../README.md) - 项目说明
- [main.md](../main.md) - 使用指南
- [L4_GPU_DEPENDENCIES.md](../L4_GPU_DEPENDENCIES.md) - GPU 环境配置
- [web/CHAPTER_REVIEW_README.md](../web/CHAPTER_REVIEW_README.md) - 审核系统说明

---

**最后更新**: 2025-01-18
**版本**: 1.0.0

