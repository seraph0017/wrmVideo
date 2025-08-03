#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from volcenginesdkarkruntime import Ark

# 测试API调用
api_key = "acfece44-4672-4578-86cf-99e317954a32"
client = Ark(api_key=api_key)
model = "doubao-seed-1-6-flash-250615"

# 简单测试
test_prompt = "请用中文回答：今天天气怎么样？"

try:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": test_prompt}
        ],
        stream=False
    )
    
    response = completion.choices[0].message.content
    print(f"API响应: {response}")
    print(f"响应长度: {len(response)}")
    print(f"响应类型: {type(response)}")
    
    # 检查是否有编码问题
    print(f"响应的前100个字符: {repr(response[:100])}")
    
except Exception as e:
    print(f"API调用失败: {e}")