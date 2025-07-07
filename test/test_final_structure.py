#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终项目结构测试
验证重构后的完整项目结构和功能
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_project_structure():
    """测试项目结构"""
    print("测试项目结构...")
    
    # 检查关键目录
    required_dirs = [
        'config',
        'src/pic',
        'src/voice', 
        'src/script',
        'test',
        'data'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"✗ 缺少目录: {missing_dirs}")
        return False
    else:
        print("✓ 项目目录结构正确")
        return True

def test_config_files():
    """测试配置文件"""
    print("测试配置文件...")
    
    config_files = [
        'config/prompt_config.py',
        'config/config.example.py'
    ]
    
    missing_files = []
    for file_path in config_files:
        full_path = os.path.join(project_root, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ 缺少配置文件: {missing_files}")
        return False
    else:
        print("✓ 配置文件完整")
        return True

def test_module_files():
    """测试模块文件"""
    print("测试模块文件...")
    
    module_files = [
        'src/pic/gen_pic.py',
        'src/voice/gen_voice.py',
        'src/script/gen_script.py'
    ]
    
    missing_files = []
    for file_path in module_files:
        full_path = os.path.join(project_root, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ 缺少模块文件: {missing_files}")
        return False
    else:
        print("✓ 模块文件完整")
        return True

def test_template_files():
    """测试模板文件"""
    print("测试模板文件...")
    
    template_files = [
        'src/pic/pic_generation.j2',
        'src/voice/voice_config.j2',
        'src/script/script_generation.j2'
    ]
    
    missing_files = []
    for file_path in template_files:
        full_path = os.path.join(project_root, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ 缺少模板文件: {missing_files}")
        return False
    else:
        print("✓ 模板文件完整")
        return True

def test_old_files_removed():
    """测试旧文件是否已删除"""
    print("测试旧文件清理...")
    
    old_files = [
        'src/gen_pic.py',
        'src/gen_voice.py',
        'src/gen_script.py',
        'src/config.py',
        'src/config.example.py'
    ]
    
    old_dirs = [
        'templates'
    ]
    
    remaining_files = []
    for file_path in old_files:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            remaining_files.append(file_path)
    
    remaining_dirs = []
    for dir_path in old_dirs:
        full_path = os.path.join(project_root, dir_path)
        if os.path.exists(full_path):
            remaining_dirs.append(dir_path)
    
    if remaining_files or remaining_dirs:
        print(f"✗ 仍存在旧文件/目录: {remaining_files + remaining_dirs}")
        return False
    else:
        print("✓ 旧文件已清理")
        return True

def test_imports():
    """测试导入功能"""
    print("测试模块导入...")
    
    try:
        # 测试配置导入
        from config.config import TTS_CONFIG, ARK_CONFIG, IMAGE_CONFIG
        from config.prompt_config import prompt_config, ART_STYLES, VOICE_PRESETS
        
        # 测试模块导入
        from src.pic.gen_pic import generate_image_with_style, list_available_styles
        from src.voice.gen_voice import VoiceGenerator, list_available_presets
        from src.script.gen_script import ScriptGenerator
        
        print("✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_template_loading():
    """测试模板加载"""
    print("测试模板加载...")
    
    try:
        from config.prompt_config import prompt_config
        
        # 测试图片模板
        pic_prompt = prompt_config.get_pic_prompt("测试描述", "manga")
        if not pic_prompt:
            print("✗ 图片模板加载失败")
            return False
        
        # 测试脚本模板
        script_prompt = prompt_config.get_script_prompt("测试内容")
        if not script_prompt:
            print("✗ 脚本模板加载失败")
            return False
        
        # 测试语音模板
        voice_config = prompt_config.get_voice_config("测试文本", "test-id", {"appid": "test"})
        if not voice_config:
            print("✗ 语音模板加载失败")
            return False
        
        print("✓ 所有模板加载成功")
        return True
    except Exception as e:
        print(f"✗ 模板加载失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 最终项目结构测试 ===")
    print()
    
    tests = [
        ("项目结构", test_project_structure),
        ("配置文件", test_config_files),
        ("模块文件", test_module_files),
        ("模板文件", test_template_files),
        ("旧文件清理", test_old_files_removed),
        ("模块导入", test_imports),
        ("模板加载", test_template_loading)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 项目重构完全成功！")
        print("\n重构成果:")
        print("✅ 删除了旧模块文件")
        print("✅ 将模板文件移动到对应模块目录")
        print("✅ 更新了所有引用路径")
        print("✅ 保持了功能完整性")
        print("✅ 项目结构更加清晰")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败，需要进一步检查。")
    
    return passed == total

if __name__ == '__main__':
    main()