#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from volcenginesdkarkruntime import Ark
from jinja2 import Environment, FileSystemLoader

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.config import ARK_CONFIG

def debug_generate_chapter_narration(chapter_content, chapter_num, total_chapters):
    """
    调试版本的章节解说生成函数
    """
    try:
        # 初始化API客户端
        api_key = ARK_CONFIG.get('api_key') or os.getenv('ARK_API_KEY')
        if not api_key:
            raise ValueError("请设置ARK_API_KEY环境变量或在config.py中配置api_key参数")
        
        client = Ark(api_key=api_key)
        model = ARK_CONFIG.get('model', 'doubao-seed-1-6-flash-250615')
        
        print(f"=== 调试信息 ===")
        print(f"API Key: {api_key[:10]}...")
        print(f"Model: {model}")
        print(f"章节内容长度: {len(chapter_content)}")
        
        # 设置模板目录
        template_dir = os.path.dirname(__file__)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('chapter_narration_prompt.j2')
        
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
        
        # 渲染模板
        custom_prompt = template.render(
            chapter_num=chapter_num,
            total_chapters=total_chapters,
            chapter_content=chapter_content,
            characters=characters
        )
        
        print(f"Prompt长度: {len(custom_prompt)}")
        print(f"Prompt前200字符: {custom_prompt[:200]}")
        
        print(f"正在为第{chapter_num}章生成解说文案...")
        
        # 调用API生成解说
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": custom_prompt}
            ],
            stream=False
        )
        
        narration = completion.choices[0].message.content.strip()
        print(f"第{chapter_num}章解说文案生成完成，长度：{len(narration)}字")
        print(f"生成内容前200字符: {repr(narration[:200])}")
        
        return narration
        
    except Exception as e:
        print(f"生成第{chapter_num}章解说文案时出错：{e}")
        import traceback
        traceback.print_exc()
        return ""

def main():
    # 读取测试章节内容
    chapter_file = "/Users/xunan/Projects/wrmProject/data/002/chapter_001/original_content.txt"
    
    if not os.path.exists(chapter_file):
        print(f"文件不存在: {chapter_file}")
        return
    
    with open(chapter_file, 'r', encoding='utf-8') as f:
        chapter_content = f.read()
    
    print(f"读取章节内容，长度: {len(chapter_content)}")
    
    # 生成解说
    narration = debug_generate_chapter_narration(chapter_content, 1, 2)
    
    if narration:
        # 保存到调试文件
        debug_file = "/Users/xunan/Projects/wrmProject/debug_narration.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(narration)
        print(f"调试解说已保存到: {debug_file}")
    else:
        print("解说生成失败")

if __name__ == "__main__":
    main()