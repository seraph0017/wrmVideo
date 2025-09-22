#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_gen_image_v3.py - 测试gen_image_async_v3.py的功能

测试内容：
1. 方舟SDK连接测试
2. 配置文件读取测试
3. 基本图片生成功能测试
"""

import os
import sys
import tempfile
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import ARK_CONFIG
from volcenginesdkarkruntime import Ark


def test_ark_config():
    """测试方舟配置"""
    print("=== 测试方舟配置 ===")
    
    print(f"Base URL: {ARK_CONFIG['base_url']}")
    print(f"API Key (前8位): {ARK_CONFIG['t2i_v3'][:8]}...")
    print(f"Model: doubao-seedream-3-0-t2i-250415")
    
    return True


def test_ark_connection():
    """测试方舟SDK连接"""
    print("\n=== 测试方舟SDK连接 ===")
    
    try:
        # 初始化客户端
        client = Ark(
            base_url=ARK_CONFIG['base_url'],
            api_key=ARK_CONFIG['t2i_v3']
        )
        
        print("✓ 方舟客户端初始化成功")
        return client
        
    except Exception as e:
        print(f"✗ 方舟客户端初始化失败: {e}")
        return None


def test_simple_image_generation(client):
    """测试简单图片生成"""
    print("\n=== 测试简单图片生成 ===")
    
    if not client:
        print("✗ 客户端未初始化，跳过测试")
        return False
    
    try:
        # 简单的测试prompt
        test_prompt = "一只可爱的小猫咪，坐在花园里，阳光明媚，卡通风格"
        
        print(f"测试Prompt: {test_prompt}")
        print("正在生成图片...")
        
        # 调用API
        images_response = client.images.generate(
            model="doubao-seedream-3-0-t2i-250415",
            prompt=test_prompt
        )
        
        # 检查响应
        if images_response and images_response.data and len(images_response.data) > 0:
            image_url = images_response.data[0].url
            print(f"✓ 图片生成成功")
            print(f"图片URL: {image_url}")
            return True
        else:
            print("✗ 图片生成失败，响应为空")
            return False
            
    except Exception as e:
        print(f"✗ 图片生成失败: {e}")
        return False


def test_narration_parser():
    """测试narration解析器"""
    print("\n=== 测试narration解析器 ===")
    
    try:
        # 导入解析器
        from gen_image_async_v3 import NarrationParser
        
        # 创建测试narration内容
        test_narration = """
<角色1>
<姓名>李明</姓名>
<性别>Male</性别>
<年龄段>青年</年龄段>
<外貌特征>
<发型>短发</发型>
<发色>黑色</发色>
<面部特征>英俊的面容，剑眉星目</面部特征>
<身材特征>身材高大挺拔</身材特征>
</外貌特征>
<服装风格>
<上衣>白色长袍</上衣>
<下装>黑色长裤</下装>
<配饰>腰间佩剑</配饰>
</服装风格>
</角色1>

<分镜1>
<图片特写1>
<角色姓名>李明</角色姓名>
<解说内容>李明站在山顶，眺望远方</解说内容>
<图片prompt>一位英俊的青年男子站在山顶，背景是连绵的群山，夕阳西下</图片prompt>
</图片特写1>
</分镜1>
"""
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_narration)
            temp_file = f.name
        
        try:
            # 测试解析
            parser = NarrationParser(temp_file)
            characters = parser.parse_characters()
            scenes = parser.parse_scenes()
            
            print(f"✓ 解析到 {len(characters)} 个角色")
            print(f"✓ 解析到 {len(scenes)} 个场景")
            
            if characters:
                print(f"角色信息: {list(characters.keys())}")
            
            if scenes:
                print(f"场景信息: {scenes[0].get('character', 'N/A')}")
            
            return True
            
        finally:
            # 清理临时文件
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"✗ narration解析器测试失败: {e}")
        return False


def test_prompt_builder():
    """测试prompt构建器"""
    print("\n=== 测试prompt构建器 ===")
    
    try:
        from gen_image_async_v3 import ImagePromptBuilder
        
        # 创建测试角色信息
        character_info = {
            'name': '李明',
            'gender': 'Male',
            'appearance': {
                'face': '英俊的面容，剑眉星目',
                'hair_style': '短发',
                'hair_color': '黑色',
                'body': '身材高大挺拔'
            },
            'clothing': {
                'top': '白色长袍',
                'bottom': '黑色长裤',
                'accessory': '腰间佩剑'
            }
        }
        
        scene_prompt = "一位英俊的青年男子站在山顶，背景是连绵的群山，夕阳西下"
        
        # 测试构建器
        builder = ImagePromptBuilder()
        character_desc = builder.build_character_description(character_info)
        complete_prompt = builder.build_complete_prompt(character_info, scene_prompt)
        
        print(f"✓ 角色描述: {character_desc}")
        print(f"✓ 完整prompt: {complete_prompt[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ prompt构建器测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试gen_image_async_v3.py功能")
    print("=" * 50)
    
    # 测试配置
    config_ok = test_ark_config()
    
    # 测试连接
    client = test_ark_connection()
    
    # 测试解析器
    parser_ok = test_narration_parser()
    
    # 测试prompt构建器
    builder_ok = test_prompt_builder()
    
    # 测试图片生成（可选，需要API调用）
    print("\n是否要测试实际的图片生成？(y/n): ", end="")
    user_input = input().strip().lower()
    
    image_ok = True
    if user_input == 'y':
        image_ok = test_simple_image_generation(client)
    else:
        print("跳过图片生成测试")
    
    # 总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"配置测试: {'✓' if config_ok else '✗'}")
    print(f"连接测试: {'✓' if client else '✗'}")
    print(f"解析器测试: {'✓' if parser_ok else '✗'}")
    print(f"构建器测试: {'✓' if builder_ok else '✗'}")
    print(f"图片生成测试: {'✓' if image_ok else '✗'}")
    
    all_ok = config_ok and client and parser_ok and builder_ok and image_ok
    print(f"\n整体测试结果: {'✓ 全部通过' if all_ok else '✗ 存在问题'}")
    
    return all_ok


if __name__ == "__main__":
    main()