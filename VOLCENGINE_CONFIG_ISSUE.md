# 火山引擎配置问题说明

## 问题描述
当前项目中出现 "Access Denied" 错误，原因是火山引擎视觉服务的密钥配置不正确。

## 问题分析

1. **密钥混用问题**：
   - 当前 `.env` 文件中的 `VOLCENGINE_ACCESS_KEY` 和 `VOLCENGINE_SECRET_KEY` 与 `TOS_ACCESS_KEY` 和 `TOS_SECRET_KEY` 相同
   - 这是错误的，因为：
     - TOS (Torch Object Storage) 是火山引擎的对象存储服务
     - 视觉服务 (Visual Service) 是火山引擎的AI图片生成服务
     - 这两个服务需要不同的访问密钥

2. **当前配置状态**：
   ```
   VOLCENGINE_ACCESS_KEY=your_volcengine_access_key_here
   VOLCENGINE_SECRET_KEY=your_volcengine_secret_key_here
   TOS_ACCESS_KEY=your_tos_access_key_here
   TOS_SECRET_KEY=your_tos_secret_key_here
   ```

## 解决方案

### 步骤1：获取正确的火山引擎视觉服务密钥

1. 登录火山引擎控制台：https://console.volcengine.com/
2. 进入 "视觉智能" 或 "AI服务" 部分
3. 找到 "图像生成" 或类似的服务
4. 获取该服务专用的 Access Key 和 Secret Key

### 步骤2：更新配置文件

在 `.env` 文件中更新火山引擎视觉服务的密钥：
```bash
# 保持 TOS 配置不变（用于对象存储）
TOS_ACCESS_KEY=your_actual_tos_access_key
TOS_SECRET_KEY=your_actual_tos_secret_key

# 更新为正确的火山引擎视觉服务密钥
VOLCENGINE_ACCESS_KEY=your_actual_volcengine_access_key
VOLCENGINE_SECRET_KEY=your_actual_volcengine_secret_key
```

### 步骤3：重启服务

更新配置后，需要重启 Celery worker：
```bash
# 停止当前 worker
celery -A web control shutdown

# 重新启动 worker
celery -A web worker --loglevel=info
```

## 验证方法

运行测试脚本验证配置：
```bash
cd web
python test_django_volcengine.py
```

成功的输出应该显示 API 调用成功，而不是 "Access Denied" 错误。

## 注意事项

1. **服务区分**：确保使用的是火山引擎视觉服务的密钥，不是 TOS 存储服务的密钥
2. **权限检查**：确保获取的密钥具有图片生成服务的访问权限
3. **密钥格式**：密钥应该是原始格式，无需 Base64 编码/解码
4. **安全性**：不要在代码中硬编码密钥，始终使用环境变量

## 相关文件

- `.env` - 环境变量配置文件
- `web/web/settings.py` - Django 设置文件
- `config/config.py` - 项目配置文件
- `web/video/tasks.py` - Celery 任务文件（使用火山引擎API）