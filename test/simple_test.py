#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from volcenginesdkarkruntime import Ark

# 测试简化版本的章节解说生成
api_key = "acfece44-4672-4578-86cf-99e317954a32"
client = Ark(api_key=api_key)
model = "doubao-seed-1-6-flash-250615"

# 读取章节内容（只取前1000字符进行测试）
chapter_file = "/Users/xunan/Projects/wrmProject/data/002/chapter_001/original_content.txt"

with open(chapter_file, 'r', encoding='utf-8') as f:
    full_content = f.read()
    # 只取前1000字符
    chapter_content = full_content[:1000]

print(f"测试章节内容长度: {len(chapter_content)}")
print(f"章节内容预览: {chapter_content[:200]}...")

# 简化的prompt
simple_prompt = f"""
请根据以下小说章节内容，生成10个分镜的解说文案。每个分镜包含解说内容和图片描述。

要求：
1. 每个分镜的解说内容要详细生动
2. 总字数达到1200字左右
3. 按照XML格式输出

小说章节内容：
{chapter_content}

请按照以下格式输出：
<第1章节>
<分镜1>
<解说内容>这里是第一个分镜的解说内容...</解说内容>
<图片prompt>这里是第一个分镜的图片描述...</图片prompt>
</分镜1>
<分镜2>
<解说内容>这里是第二个分镜的解说内容...</解说内容>
<图片prompt>这里是第二个分镜的图片描述...</图片prompt>
</分镜2>
... (继续到分镜10)
</第1章节>
"""

print(f"\n简化Prompt长度: {len(simple_prompt)}")

try:
    print("\n开始API调用...")
    
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": simple_prompt}
        ],
        stream=False
    )
    
    response = completion.choices[0].message.content.strip()
    
    print(f"\n=== API响应 ===")
    print(f"响应长度: {len(response)}字符")
    print(f"响应前500字符:")
    print(response[:500])
    
    # 保存简化版本的结果
    simple_file = "/Users/xunan/Projects/wrmProject/simple_narration.txt"
    with open(simple_file, 'w', encoding='utf-8') as f:
        f.write(response)
    print(f"\n简化版解说已保存到: {simple_file}")
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()