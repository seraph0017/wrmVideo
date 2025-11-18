# 🚀 部署工具包

本目录包含 wrmVideo 项目的完整部署工具和脚本。

## 📁 目录结构

```
deploy/
├── DEPLOYMENT.md           # 完整部署文档
├── README.md              # 本文件
├── deploy.sh              # 一键部署脚本
├── check_environment.py   # 环境检查工具
├── service_manager.sh     # 服务管理脚本
├── backup.sh              # 数据备份脚本
└── restore.sh             # 数据恢复脚本
```

## 📖 文档

### [DEPLOYMENT.md](DEPLOYMENT.md)

完整的部署文档，包含：

- 环境要求和依赖说明
- 详细的部署步骤
- 配置文件说明
- 服务管理指南
- 备份与恢复方案
- 故障排查指南
- 性能优化建议

**适用场景**：首次部署、生产环境部署、详细了解部署流程

## 🛠️ 脚本工具

### 1. deploy.sh - 一键部署脚本

自动化部署脚本，完成从环境检查到服务启动的全流程。

**功能**：
- 检查系统环境和依赖
- 安装必需软件
- 创建 Python 虚拟环境
- 配置项目文件
- 初始化数据库
- 启动服务

**使用方法**：

```bash
# 开发环境部署
bash deploy.sh --dev

# 生产环境部署
bash deploy.sh --prod

# 跳过环境检查
bash deploy.sh --skip-check

# 查看帮助
bash deploy.sh --help
```

**适用场景**：快速部署、自动化部署、标准化部署流程

---

### 2. check_environment.py - 环境检查工具

检测系统环境是否满足部署要求。

**检查项目**：
- 操作系统和 Python 版本
- 必需软件（FFmpeg、MySQL、Redis）
- Python 依赖包
- GPU 环境（可选）
- 目录结构和权限
- 服务运行状态

**使用方法**：

```bash
# 运行环境检查
python deploy/check_environment.py

# 查看检查报告
cat deploy/environment_check_report.txt
cat deploy/environment_check_report.json
```

**输出**：
- 终端输出：实时检查结果
- `environment_check_report.txt`：文本格式报告
- `environment_check_report.json`：JSON 格式报告

**适用场景**：部署前检查、环境验证、问题诊断

---

### 3. service_manager.sh - 服务管理脚本

统一管理所有服务的启动、停止和重启。

**管理的服务**：
- Web 服务（Gunicorn）
- Celery Worker（异步任务处理）
- Celery Beat（定时任务调度）

**使用方法**：

```bash
# 启动所有服务
bash deploy/service_manager.sh start

# 停止所有服务
bash deploy/service_manager.sh stop

# 重启所有服务
bash deploy/service_manager.sh restart

# 查看服务状态
bash deploy/service_manager.sh status

# 查看服务日志
bash deploy/service_manager.sh logs

# 管理单个服务
bash deploy/service_manager.sh start web      # 启动 Web 服务
bash deploy/service_manager.sh stop celery    # 停止 Celery Worker
bash deploy/service_manager.sh restart beat   # 重启 Celery Beat
bash deploy/service_manager.sh logs web       # 查看 Web 日志

# 查看帮助
bash deploy/service_manager.sh help
```

**日志位置**：
- Web 访问日志：`logs/gunicorn_access.log`
- Web 错误日志：`logs/gunicorn_error.log`
- Celery Worker 日志：`logs/celery_worker.log`
- Celery Beat 日志：`logs/celery_beat.log`

**适用场景**：日常运维、服务管理、故障排查

---

### 4. backup.sh - 数据备份脚本

自动备份项目数据和配置。

**备份内容**：
- 数据库（MySQL/SQLite）
- 配置文件（config/）
- 数据目录（data/）
- 角色图片（Character_Images/）
- Web 媒体文件（web/media/）

**使用方法**：

```bash
# 完整备份
bash deploy/backup.sh

# 仅备份数据库
bash deploy/backup.sh --db-only

# 仅备份配置
bash deploy/backup.sh --config-only

# 仅备份数据
bash deploy/backup.sh --data-only

# 指定输出目录
bash deploy/backup.sh --output /path/to/backup

# 查看帮助
bash deploy/backup.sh --help
```

**备份位置**：
- 默认：`backups/backup_YYYYMMDD_HHMMSS/`
- 自定义：使用 `--output` 参数指定

**备份文件**：
- `database.sql.gz` 或 `db.sqlite3`：数据库备份
- `config.tar.gz`：配置文件
- `data.tar.gz`：数据目录
- `character_images.tar.gz`：角色图片
- `media.tar.gz`：媒体文件
- `MANIFEST.txt`：备份清单

**自动备份**：

```bash
# 添加到 crontab，每天凌晨 2 点自动备份
crontab -e

# 添加以下行
0 2 * * * /path/to/wrmVideo/deploy/backup.sh
```

**适用场景**：定期备份、升级前备份、数据迁移

---

### 5. restore.sh - 数据恢复脚本

从备份恢复项目数据和配置。

**恢复内容**：
- 数据库
- 配置文件
- 数据目录
- 角色图片
- Web 媒体文件

**使用方法**：

```bash
# 完整恢复
bash deploy/restore.sh /path/to/backup_20250118_120000

# 仅恢复数据库
bash deploy/restore.sh /path/to/backup_20250118_120000 --db-only

# 仅恢复配置
bash deploy/restore.sh /path/to/backup_20250118_120000 --config-only

# 仅恢复数据
bash deploy/restore.sh /path/to/backup_20250118_120000 --data-only

# 强制覆盖（不询问）
bash deploy/restore.sh /path/to/backup_20250118_120000 --force

# 查看帮助
bash deploy/restore.sh --help
```

**注意事项**：
- 恢复操作会覆盖现有文件
- 建议在恢复前先备份当前数据
- 恢复后需要重启服务

**适用场景**：数据恢复、系统迁移、回滚操作

---

## 🔄 典型部署流程

### 首次部署

```bash
# 1. 检查环境
python deploy/check_environment.py

# 2. 一键部署
bash deploy/deploy.sh --prod

# 3. 验证服务
bash deploy/service_manager.sh status
```

### 日常运维

```bash
# 启动服务
bash deploy/service_manager.sh start

# 查看状态
bash deploy/service_manager.sh status

# 查看日志
bash deploy/service_manager.sh logs

# 停止服务
bash deploy/service_manager.sh stop
```

### 数据备份

```bash
# 手动备份
bash deploy/backup.sh

# 设置自动备份
crontab -e
# 添加：0 2 * * * /path/to/wrmVideo/deploy/backup.sh
```

### 系统升级

```bash
# 1. 备份数据
bash deploy/backup.sh

# 2. 停止服务
bash deploy/service_manager.sh stop

# 3. 更新代码
git pull origin main

# 4. 更新依赖
pip install -r requirements.txt --upgrade

# 5. 数据库迁移
cd web
python manage.py migrate

# 6. 重启服务
cd ..
bash deploy/service_manager.sh restart
```

### 故障恢复

```bash
# 1. 停止服务
bash deploy/service_manager.sh stop

# 2. 恢复数据
bash deploy/restore.sh /path/to/backup_20250118_120000

# 3. 重启服务
bash deploy/service_manager.sh restart

# 4. 验证服务
bash deploy/service_manager.sh status
```

## 📊 监控与维护

### 日志查看

```bash
# 查看所有服务日志
bash deploy/service_manager.sh logs

# 实时监控日志
tail -f logs/gunicorn_error.log
tail -f logs/celery_worker.log

# 查看最近的错误
grep ERROR logs/gunicorn_error.log | tail -n 50
```

### 服务健康检查

```bash
# 检查服务状态
bash deploy/service_manager.sh status

# 检查端口占用
lsof -i :8000

# 检查进程
ps aux | grep gunicorn
ps aux | grep celery
```

### 磁盘空间管理

```bash
# 查看磁盘使用
df -h

# 查看目录大小
du -sh data/
du -sh Character_Images/
du -sh backups/

# 清理旧备份（保留最近 30 天）
find backups/ -name "backup_*" -type d -mtime +30 -exec rm -rf {} \;
```

## 🆘 故障排查

### 服务无法启动

```bash
# 1. 查看错误日志
bash deploy/service_manager.sh logs

# 2. 检查端口占用
lsof -i :8000

# 3. 检查数据库连接
python web/manage.py dbshell

# 4. 重新检查环境
python deploy/check_environment.py
```

### 数据库问题

```bash
# 检查 MySQL 服务
sudo systemctl status mysql

# 测试数据库连接
mysql -u wrmvideo -p -e "SELECT 1;"

# 重新执行迁移
cd web
python manage.py migrate
```

### Celery 任务不执行

```bash
# 检查 Redis 连接
redis-cli ping

# 查看 Celery 日志
tail -f logs/celery_worker.log

# 重启 Celery
bash deploy/service_manager.sh restart celery
```

## 📞 获取帮助

如遇到问题：

1. 查看 [DEPLOYMENT.md](DEPLOYMENT.md) 完整文档
2. 运行环境检查：`python deploy/check_environment.py`
3. 查看日志文件：`bash deploy/service_manager.sh logs`
4. 查看故障排查章节
5. 联系技术支持团队

## 📝 更新日志

- **2025-01-18**: 初始版本
  - 创建完整的部署工具包
  - 提供一键部署、服务管理、备份恢复等功能
  - 完善的文档和使用说明

---

**最后更新**: 2025-01-18

