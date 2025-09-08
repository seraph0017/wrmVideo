#!/usr/bin/env python
import os
import sys

# 添加项目路径
sys.path.append('/Users/xunan/Projects/wrmVideo/web')

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')

import django
django.setup()

from video.models import Character
from video.views import find_character_image_in_chapter

def test_character_image():
    print("=== 测试角色图片查找功能 ===")
    
    # 获取角色信息
    character = Character.objects.get(id=20)
    print(f"角色ID: {character.id}")
    print(f"角色名称: {character.name}")
    
    # 测试参数
    novel_id = "13"
    chapter_id = "48"
    chapter_path = f"data/{novel_id.zfill(3)}/chapter_{chapter_id.zfill(3)}"
    
    print(f"\n章节路径: {chapter_path}")
    
    # 检查目录是否存在
    project_root = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(project_root, chapter_path, "images")
    print(f"项目根目录: {project_root}")
    print(f"图片目录: {images_dir}")
    print(f"图片目录是否存在: {os.path.exists(images_dir)}")
    
    if os.path.exists(images_dir):
        files = os.listdir(images_dir)
        print(f"目录中的文件: {files}")
        
        for filename in files:
            print(f"检查文件: {filename}")
            if character.name in filename:
                print(f"  -> 匹配角色名称: {character.name}")
            else:
                print(f"  -> 不匹配角色名称: {character.name}")
    
    # 调用函数测试
    print(f"\n调用 find_character_image_in_chapter...")
    result = find_character_image_in_chapter(chapter_path, character.name)
    print(f"函数返回结果: {result}")

if __name__ == "__main__":
    test_character_image()