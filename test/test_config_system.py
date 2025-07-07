#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置化系统测试脚本
测试新的Jinja2模板配置系统是否正常工作
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_prompt_config_import():
    """
    测试配置模块导入
    """
    print("测试配置模块导入...")
    try:
        from config.prompt_config import (
            prompt_config, ART_STYLES, VOICE_PRESETS, 
            SCRIPT_CONFIG, get_art_style_list, get_voice_preset_list
        )
        print("✓ 配置模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 配置模块导入失败：{e}")
        return False

def test_art_styles():
    """
    测试艺术风格配置
    """
    print("\n测试艺术风格配置...")
    try:
        from config.prompt_config import ART_STYLES, get_art_style_list, validate_style
        
        # 测试风格列表
        styles = get_art_style_list()
        print(f"可用艺术风格：{styles}")
        
        # 测试风格验证
        valid_style = validate_style('manga')
        invalid_style = validate_style('invalid_style')
        
        assert valid_style == True, "manga风格应该有效"
        assert invalid_style == False, "无效风格应该返回False"
        
        print("✓ 艺术风格配置测试通过")
        return True
    except Exception as e:
        print(f"✗ 艺术风格配置测试失败：{e}")
        return False

def test_voice_presets():
    """
    测试语音预设配置
    """
    print("\n测试语音预设配置...")
    try:
        from config.prompt_config import VOICE_PRESETS, get_voice_preset_list, validate_voice_preset
        
        # 测试预设列表
        presets = get_voice_preset_list()
        print(f"可用语音预设：{presets}")
        
        # 测试预设验证
        valid_preset = validate_voice_preset('default')
        invalid_preset = validate_voice_preset('invalid_preset')
        
        assert valid_preset == True, "default预设应该有效"
        assert invalid_preset == False, "无效预设应该返回False"
        
        print("✓ 语音预设配置测试通过")
        return True
    except Exception as e:
        print(f"✗ 语音预设配置测试失败：{e}")
        return False

def test_pic_prompt_generation():
    """
    测试图片prompt生成
    """
    print("\n测试图片prompt生成...")
    try:
        from config.prompt_config import prompt_config
        
        # 测试不同风格的prompt生成
        test_description = "一个美丽的古代城市"
        
        for style in ['manga', 'realistic', 'watercolor']:
            prompt = prompt_config.get_pic_prompt(
                description=test_description,
                style=style
            )
            print(f"风格 {style} 的prompt：{prompt[:100]}...")
            assert len(prompt) > 0, f"{style}风格的prompt不应为空"
        
        print("✓ 图片prompt生成测试通过")
        return True
    except Exception as e:
        print(f"✗ 图片prompt生成测试失败：{e}")
        return False

def test_script_prompt_generation():
    """
    测试脚本prompt生成
    """
    print("\n测试脚本prompt生成...")
    try:
        from config.prompt_config import prompt_config
        
        test_content = "这是一个测试小说内容，用于验证脚本生成功能。"
        
        # 测试单块处理
        prompt_single = prompt_config.get_script_prompt(
            content=test_content,
            is_chunk=False
        )
        print(f"单块处理prompt长度：{len(prompt_single)}")
        assert len(prompt_single) > 0, "单块处理prompt不应为空"
        
        # 测试分块处理
        prompt_chunk = prompt_config.get_script_prompt(
            content=test_content,
            is_chunk=True,
            chunk_index=0,
            total_chunks=3
        )
        print(f"分块处理prompt长度：{len(prompt_chunk)}")
        assert len(prompt_chunk) > 0, "分块处理prompt不应为空"
        
        print("✓ 脚本prompt生成测试通过")
        return True
    except Exception as e:
        print(f"✗ 脚本prompt生成测试失败：{e}")
        return False

def test_voice_config_generation():
    """
    测试语音配置生成
    """
    print("\n测试语音配置生成...")
    try:
        from config.prompt_config import prompt_config
        
        test_text = "这是一个测试文本"
        test_request_id = "test-123"
        test_tts_config = {
            "appid": "test_app",
            "cluster": "test_cluster",
            "voice_type": "test_voice"
        }
        
        # 测试配置生成
        config = prompt_config.get_voice_config(
            text=test_text,
            request_id=test_request_id,
            tts_config=test_tts_config
        )
        
        print(f"生成的配置类型：{type(config)}")
        assert isinstance(config, dict), "配置应该是字典类型"
        assert 'request' in config, "配置应该包含request字段"
        assert config['request']['text'] == test_text, "文本应该正确设置"
        
        print("✓ 语音配置生成测试通过")
        return True
    except Exception as e:
        print(f"✗ 语音配置生成测试失败：{e}")
        return False

def test_new_modules_import():
    """
    测试新模块导入
    """
    print("\n测试新模块导入...")
    try:
        # 测试图片模块
        from src.pic.gen_pic import generate_image_with_style, list_available_styles
        print("✓ 新图片模块导入成功")
        
        # 测试语音模块
        from src.voice.gen_voice import VoiceGenerator, list_available_presets
        print("✓ 新语音模块导入成功")
        
        # 测试脚本模块
        from src.script.gen_script import ScriptGenerator
        print("✓ 新脚本模块导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 新模块导入失败：{e}")
        return False

def main():
    """
    主测试函数
    """
    print("配置化系统测试")
    print("=" * 50)
    
    tests = [
        test_prompt_config_import,
        test_art_styles,
        test_voice_presets,
        test_pic_prompt_generation,
        test_script_prompt_generation,
        test_voice_config_generation,
        test_new_modules_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果：{passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！配置化系统工作正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查配置。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)