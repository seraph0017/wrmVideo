#!/usr/bin/env python3
import sys
from validate_narration import validate_narration_file
from config.config import ARK_CONFIG
from volcenginesdkarkruntime import Ark

# 检查单个narration.txt文件
narration_file = "data/025/chapter_001/narration.txt"

# 初始化客户端
api_key = ARK_CONFIG.get("api_key")
if api_key:
    client = Ark(api_key=api_key)
else:
    client = None
    print("警告: 未配置API密钥，将跳过LLM修复")

print(f"检查文件: {narration_file}")
result = validate_narration_file(
    narration_file, 
    client=client,
    auto_fix_structure=True
)

print(f"XML结构验证: {'通过' if result['structure_validation']['valid'] else '失败'}")
if not result['structure_validation']['valid']:
    issues = result['structure_validation']['issues']
    print(f"检测到{len(issues)}个XML结构问题:")
    for issue in issues:
        print(f"  分镜{issue['scene_number']}: {issue['issue_type']} - {issue['details']}")
