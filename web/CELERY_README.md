# Celery任务队列管理指南

本项目使用Celery作为异步任务队列系统，用于处理视频生成、音频处理、图片生成等耗时操作。

## 📋 目录结构

```
web/
├── run_celery.py          # Celery管理脚本（Python版本）
├── start_celery.sh         # Celery快速启动脚本（Shell版本）
├── web/celery.py          # Celery配置文件
├── video/tasks.py         # 异步任务定义
└── CELERY_README.md       # 本文档
```

## 🚀 快速开始

### 1. 环境准备

确保以下服务正在运行：

```bash
# 启动Redis（作为消息代理）
brew services start redis

# 启动MySQL（数据库）
brew services start mysql
```

### 2. 启动Celery服务

#### 方式一：使用Shell脚本（推荐）

```bash
# 进入web目录
cd web

# 同时启动worker和beat调度器（最常用）
./start_celery.sh both

# 或者分别启动
./start_celery.sh worker    # 启动worker
./start_celery.sh beat      # 启动beat调度器

# 查看状态
./start_celery.sh status

# 停止所有Celery进程
./start_celery.sh stop
```

#### 方式二：使用Python脚本

```bash
# 进入web目录
cd web

# 同时启动worker和beat
python run_celery.py both

# 或者分别启动
python run_celery.py worker --concurrency 4  # 启动worker，设置并发数
python run_celery.py beat                    # 启动beat调度器

# 查看状态
python run_celery.py status

# 清空任务队列
python run_celery.py purge

# 启动监控
python run_celery.py monitor
```

## 📊 任务监控

### 查看Celery状态

```bash
# 使用脚本查看
./start_celery.sh status

# 或者直接使用celery命令
python -m celery -A web inspect active      # 查看活跃任务
python -m celery -A web inspect registered  # 查看注册的任务
python -m celery -A web inspect stats       # 查看统计信息
```

### 实时监控

```bash
# 启动事件监控
python run_celery.py monitor

# 或者使用flower（需要安装）
pip install flower
celery -A web flower
```

## 🔧 配置说明

### Celery配置（settings.py）

```python
# Redis配置
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 任务路由
CELERY_TASK_ROUTES = {
    'video.tasks.*': {'queue': 'celery'},
}

# 定时任务
CELERY_BEAT_SCHEDULE = {
    'scan-all-async-tasks': {
        'task': 'video.tasks.scan_and_process_async_tasks',
        'schedule': 15.0,  # 每15秒执行一次
        'args': ('data',),
    },
    'scan-specific-async-tasks': {
        'task': 'video.tasks.scan_specific_async_tasks',
        'schedule': 15.0,
        'args': ('async_tasks',),
    },
}
```

### 主要任务类型

| 任务名称 | 描述 | 执行时间 |
|---------|------|----------|
| `test_task` | 测试任务 | 5秒 |
| `generate_video_async` | 异步生成视频 | 10分钟+ |
| `generate_character_images_async` | 生成角色图片 | 5-10分钟 |
| `generate_script_async` | 生成脚本 | 2-5分钟 |
| `generate_audio_async` | 生成音频 | 5-15分钟 |
| `scan_and_process_async_tasks` | 扫描处理异步任务 | 定时执行 |

## 🛠️ 常用操作

### 清空任务队列

```bash
# 清空所有待处理任务
./start_celery.sh purge
# 或者
python run_celery.py purge
```

### 重启Celery服务

```bash
# 停止所有进程
./start_celery.sh stop

# 等待几秒后重新启动
./start_celery.sh both
```

### 调试模式

```bash
# 以调试级别启动worker
python run_celery.py worker --loglevel debug

# 单进程模式（便于调试）
python run_celery.py worker --concurrency 1
```

## 📝 日志管理

### 日志文件位置

```
web/logs/
├── celery.log          # Celery主日志
└── django.log          # Django应用日志
```

### 查看日志

```bash
# 实时查看Celery日志
tail -f logs/celery.log

# 查看最近的错误
grep ERROR logs/celery.log | tail -20
```

## 🚨 故障排除

### 常见问题

1. **Redis连接失败**
   ```bash
   # 检查Redis是否运行
   redis-cli ping
   
   # 启动Redis
   brew services start redis
   ```

2. **Worker无法启动**
   ```bash
   # 检查Django设置
   python manage.py check
   
   # 检查数据库连接
   python manage.py migrate
   ```

3. **任务执行失败**
   ```bash
   # 查看详细错误日志
   python run_celery.py worker --loglevel debug
   
   # 清空队列重新开始
   python run_celery.py purge
   ```

4. **Beat调度器问题**
   ```bash
   # 检查数据库中的定时任务
   python manage.py shell
   >>> from django_celery_beat.models import PeriodicTask
   >>> PeriodicTask.objects.all()
   ```

### 性能优化

1. **调整并发数**
   ```bash
   # 根据CPU核心数调整
   python run_celery.py worker --concurrency 8
   ```

2. **内存优化**
   ```bash
   # 限制每个worker处理的任务数
   python -m celery -A web worker --max-tasks-per-child=1000
   ```

3. **队列分离**
   ```python
   # 在settings.py中配置不同队列
   CELERY_TASK_ROUTES = {
       'video.tasks.generate_video_async': {'queue': 'video'},
       'video.tasks.generate_audio_async': {'queue': 'audio'},
   }
   ```

## 📚 相关文档

- [Celery官方文档](https://docs.celeryproject.org/)
- [Django-Celery-Beat文档](https://django-celery-beat.readthedocs.io/)
- [Redis文档](https://redis.io/documentation)

## 🔄 开发工作流

1. **开发新任务**
   - 在 `video/tasks.py` 中定义新的 `@shared_task`
   - 重启worker以加载新任务
   - 测试任务执行

2. **部署更新**
   - 停止现有worker: `./start_celery.sh stop`
   - 更新代码
   - 重启服务: `./start_celery.sh both`

3. **监控生产环境**
   - 定期检查日志文件
   - 监控Redis内存使用
   - 关注任务执行时间和失败率

---

**注意**: 在生产环境中，建议使用进程管理工具（如supervisor、systemd）来管理Celery进程，确保服务的稳定性和自动重启能力。