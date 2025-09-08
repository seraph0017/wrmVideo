# 安全配置说明

## 环境变量配置

为了保护敏感信息，本项目使用环境变量来存储配置信息。请按照以下步骤设置：

### 1. 创建环境变量文件

复制 `.env.example` 文件并重命名为 `.env`：

```bash
cp .env.example .env
```

### 2. 配置TOS（VolcEngine）密钥

编辑 `.env` 文件，填入你的实际密钥：

```
TOS_ACCESS_KEY=你的实际access_key
TOS_SECRET_KEY=你的实际secret_key
```

### 3. 加载环境变量

在运行Django应用之前，确保环境变量已加载：

```bash
# 方法1：使用export命令
export TOS_ACCESS_KEY="你的access_key"
export TOS_SECRET_KEY="你的secret_key"

# 方法2：使用python-dotenv（推荐）
pip install python-dotenv
```

### 4. 安全注意事项

- **永远不要**将 `.env` 文件提交到版本控制系统
- **永远不要**在代码中硬编码敏感信息
- 定期更换密钥
- 确保生产环境使用不同的密钥

### 5. Git推送前检查

在推送代码前，请确保：
- `.env` 文件已被 `.gitignore` 忽略
- 代码中没有硬编码的密钥
- 使用 `git status` 检查暂存区文件

如果Git检测到敏感信息，请：
1. 移除敏感信息
2. 使用 `git reset` 撤销提交
3. 重新提交干净的代码