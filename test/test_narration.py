#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from volcenginesdkarkruntime import Ark
from jinja2 import Environment, FileSystemLoader

# 测试章节解说生成
api_key = "acfece44-4672-4578-86cf-99e317954a32"
client = Ark(api_key=api_key)
model = "doubao-seed-1-6-flash-250615"

# 读取模板
template_dir = "/Users/xunan/Projects/wrmProject"
env = Environment(loader=FileSystemLoader(template_dir))
template = env.get_template('chapter_narration_prompt.j2')

# 测试章节内容（简化版）
test_chapter = """
第1章穷得叮当响回来了
下午四点，并非是饭点。
四周都是正在施工的工地，夹在这样的环境下，小炒店即便称不上尘土飞扬，但是也着实没什么环境可言。
但小炒店老板的手艺确实不错。
严助理一直到快吃饱了才抬头悄悄地看了眼坐在对面的，与这个环境格格不入的自家老板谭辞。
"""

# 示例人物数据
characters = [
    {
        'name': '芜音',
        'height_build': '身材纤细（约165cm），体型匀称',
        'hair_color': '乌黑色',
        'hair_style': '长发',
        'hair_texture': '直发',
        'eye_color': '黑色',
        'eye_shape': '杏眼',
        'eye_expression': '眼神清澈',
        'face_shape': '瓜子脸',
        'chin_shape': '尖下巴',
        'skin_tone': '白皙',
        'clothing_color': '白色',
        'clothing_style': '古装',
        'clothing_material': '丝质',
        'glasses': '无',
        'jewelry': '无',
        'other_accessories': '无',
        'expression_posture': '给人清雅脱俗的感觉'
    },
    {
        'name': '谭辞',
        'height_build': '身材高大（约180cm），体型匀称',
        'hair_color': '乌黑色',
        'hair_style': '短发',
        'hair_texture': '直发',
        'eye_color': '深棕色',
        'eye_shape': '丹凤眼',
        'eye_expression': '眼神犀利专注',
        'face_shape': '方形脸',
        'chin_shape': '方形下巴',
        'skin_tone': '健康肤色',
        'clothing_color': '深蓝色',
        'clothing_style': '西装',
        'clothing_material': '羊毛',
        'glasses': '无',
        'jewelry': '银色手表',
        'other_accessories': '无',
        'expression_posture': '给人可靠专业的感觉'
    }
]

try:
    # 渲染模板
    custom_prompt = template.render(
        chapter_num=1,
        total_chapters=2,
        chapter_content=test_chapter,
        characters=characters
    )
    
    print("=== 生成的Prompt（前500字符）===")
    print(custom_prompt[:500])
    print("\n=== Prompt总长度 ===")
    print(f"Prompt长度: {len(custom_prompt)}字符")
    
    print("\n=== 开始API调用 ===")
    
    # 调用API生成解说
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": custom_prompt}
        ],
        stream=False
    )
    
    narration = completion.choices[0].message.content.strip()
    
    print(f"\n=== API响应 ===")
    print(f"响应长度: {len(narration)}字符")
    print(f"响应前200字符: {repr(narration[:200])}")
    print(f"\n完整响应:")
    print(narration)
    
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()