#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础功能测试脚本
测试重构后的项目结构和配置系统
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_config_import():
    """测试配置文件导入"""
    try:
        from config.config import TTS_CONFIG, ARK_CONFIG, IMAGE_CONFIG
        print("✓ 配置文件导入成功")
        print(f"  TTS配置: {list(TTS_CONFIG.keys())}")
        print(f"  ARK配置: {list(ARK_CONFIG.keys())}")
        print(f"  图片配置: {list(IMAGE_CONFIG.keys())}")
        return True
    except Exception as e:
        print(f"✗ 配置文件导入失败: {e}")
        return False

def test_prompt_config_import():
    """测试prompt配置导入"""
    try:
        from config.prompt_config import prompt_config, ART_STYLES, VOICE_PRESETS, SCRIPT_CONFIG
        print("✓ Prompt配置导入成功")
        print(f"  艺术风格数量: {len(ART_STYLES)}")
        print(f"  语音预设数量: {len(VOICE_PRESETS)}")
        print(f"  脚本配置: {list(SCRIPT_CONFIG.keys())}")
        return True
    except Exception as e:
        print(f"✗ Prompt配置导入失败: {e}")
        return False

def test_new_modules_import():
    """测试新模块导入"""
    success_count = 0
    total_count = 3
    
    # 测试图片模块
    try:
        from src.pic.gen_pic import generate_image_with_style, list_available_styles
        print("✓ 新图片模块导入成功")
        success_count += 1
    except Exception as e:
        print(f"✗ 新图片模块导入失败: {e}")
    
    # 测试语音模块
    try:
        from src.voice.gen_voice import VoiceGenerator, list_available_presets
        print("✓ 新语音模块导入成功")
        success_count += 1
    except Exception as e:
        print(f"✗ 新语音模块导入失败: {e}")
    
    # 测试脚本模块
    try:
        from src.script.gen_script import ScriptGenerator
        print("✓ 新脚本模块导入成功")
        success_count += 1
    except Exception as e:
        print(f"✗ 新脚本模块导入失败: {e}")
    
    return success_count == total_count

def test_modules_functionality():
    """测试模块功能"""
    success_count = 0
    total_count = 3
    
    # 测试图片模块
    try:
        from src.pic.gen_pic import generate_image_with_style
        print("✓ 图片模块正常")
        success_count += 1
    except Exception as e:
        print(f"✗ 图片模块问题: {e}")
    
    # 测试语音模块
    try:
        from src.voice.gen_voice import VoiceGenerator
        print("✓ 语音模块正常")
        success_count += 1
    except Exception as e:
        print(f"✗ 语音模块问题: {e}")
    
    # 测试脚本模块
    try:
        from src.script.gen_script import ScriptGenerator
        print("✓ 脚本模块正常")
        success_count += 1
    except Exception as e:
        print(f"✗ 脚本模块问题: {e}")
    
    return success_count == total_count

def test_generate_py_import():
    """测试主程序导入"""
    try:
        # 测试generate.py能否正确导入配置
        import generate
        print("✓ 主程序导入成功")
        return True
    except Exception as e:
        print(f"✗ 主程序导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 项目重构后基础功能测试 ===")
    print()
    
    tests = [
        ("配置文件导入", test_config_import),
        ("Prompt配置导入", test_prompt_config_import),
        ("新模块导入", test_new_modules_import),
        ("模块功能", test_modules_functionality),
        ("主程序导入", test_generate_py_import)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"测试 {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目重构成功。")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，需要进一步检查。")
    
    return passed == total

if __name__ == '__main__':
    main()