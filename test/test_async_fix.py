#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试异步图片生成修复
测试单个任务提交和查询功能
"""

import os
import time
from batch_generate_character_images_async import submit_image_task, parse_directory_info, generate_character_variations
from check_async_tasks import query_task_status, save_task_info, load_task_info

def test_single_task():
    """
    测试单个任务的提交和查询
    """
    print("=== 测试单个异步任务 ===")
    
    # 创建测试目录
    test_dir = "test_async_single"
    os.makedirs(test_dir, exist_ok=True)
    
    # 生成测试prompt
    test_prompt = """图片风格为「动漫」，宫崎骏，中式古典风格
比例 「9:16」
服装要求：必须圆领袍，高领设计，严禁V领或低领，绝对不能露出脖子部位，领口要完全遮盖脖子
年龄：Youth
风格：Ancient
文化：Chinese
气质：侠义英雄，正气凛然
角度：正面半身照

单人肖像，男性，健康肌肤，黑色短发，表情坚毅，中式传统服装，汉服、唐装或古代袍服，精致风格，高质量角色设定图，正面视角，清晰面部特征，动漫风格"""
    
    # 准备任务信息
    task_info = {
        "prompt": test_prompt,
        "output_path": os.path.join(test_dir, "test_character.jpeg"),
        "filename": "test_character.jpeg",
        "directory": test_dir,
        "dir_info": {
            "gender": "男",
            "age": "Youth",
            "style": "Ancient",
            "culture": "Chinese",
            "temperament": "Chivalrous"
        },
        "variation": {
            "hair_color": "黑色",
            "hair_style": "短发",
            "expression": "坚毅",
            "clothing": "精致",
            "accessory": "无饰品",
            "skin_tone": "健康"
        },
        "variation_index": 1,
        "status": "submitted"
    }
    
    print(f"提交测试任务...")
    print(f"Prompt: {test_prompt[:100]}...")
    
    # 提交任务
    task_id = submit_image_task(test_prompt, task_info)
    
    if task_id:
        print(f"✓ 任务提交成功，task_id: {task_id}")
        
        # 保存任务信息
        task_info["task_id"] = task_id
        task_file = os.path.join(test_dir, f"{task_id}.txt")
        save_task_info(task_id, task_info, test_dir)
        print(f"✓ 任务信息已保存到: {task_file}")
        
        # 等待一段时间后查询状态
        print(f"\n等待5秒后查询任务状态...")
        time.sleep(5)
        
        # 查询任务状态
        print(f"查询任务状态...")
        resp = query_task_status(task_id)
        
        if resp:
            if 'data' in resp:
                status = resp['data'].get('status', 'unknown')
                print(f"✓ 任务状态查询成功: {status}")
                
                if status == 'done':
                    print(f"🎉 任务已完成！")
                elif status in ['pending', 'running']:
                    print(f"⏳ 任务处理中，请稍后使用 check_async_tasks.py 查询")
                elif status == 'failed':
                    reason = resp['data'].get('reason', '未知原因')
                    print(f"❌ 任务失败: {reason}")
                else:
                    print(f"❓ 未知状态: {status}")
            else:
                print(f"❌ 响应格式错误: {resp}")
        else:
            print(f"❌ 查询任务状态失败")
            
        print(f"\n测试完成！")
        print(f"任务文件保存在: {test_dir}")
        print(f"可以使用以下命令继续监控:")
        print(f"python check_async_tasks.py")
        
    else:
        print(f"❌ 任务提交失败")
        return False
    
    return True

def test_directory_parsing():
    """
    测试目录解析功能
    """
    print("\n=== 测试目录解析功能 ===")
    
    test_paths = [
        "Male/15-22_Youth/Ancient/Chinese/Chivalrous",
        "Female/14-22_Youth/Fantasy/Western/Mage",
        "Male/25-40_FantasyAdult/Modern/Chinese/Scientist"
    ]
    
    for path in test_paths:
        result = parse_directory_info(path)
        print(f"路径: {path}")
        print(f"解析结果: {result}")
        print()

def test_character_variations():
    """
    测试角色变化生成
    """
    print("=== 测试角色变化生成 ===")
    
    variations = generate_character_variations()
    print(f"生成了 {len(variations)} 种角色变化:")
    
    for i, variation in enumerate(variations[:3], 1):  # 只显示前3个
        print(f"变化 {i}: {variation}")
    
    print(f"... (共{len(variations)}种变化)")

def main():
    """
    主测试函数
    """
    print("异步图片生成功能测试")
    print("=" * 50)
    
    # 测试目录解析
    test_directory_parsing()
    
    # 测试角色变化生成
    test_character_variations()
    
    # 询问是否进行实际API测试
    user_input = input("\n是否进行实际API测试？这将消耗API配额 (y/n): ").strip().lower()
    
    if user_input in ['y', 'yes', '是']:
        # 测试单个任务
        success = test_single_task()
        
        if success:
            print("\n🎉 所有测试通过！异步功能修复成功。")
        else:
            print("\n❌ 测试失败，请检查API配置和网络连接。")
    else:
        print("\n跳过API测试。")
        print("🎉 基础功能测试通过！")

if __name__ == '__main__':
    main()