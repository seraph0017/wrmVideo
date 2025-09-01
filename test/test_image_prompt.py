#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片生成prompt的脚本
基于batch_generate_character_images.py，专门用于测试不同prompt的生成效果
"""

import os
import sys
import base64
import random
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ART_STYLES 配置已移除
from config.config import IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

def generate_test_prompts():
    """
    生成多种测试prompt
    
    Returns:
        list: 包含不同测试prompt的列表
    """
    test_prompts = [
        {
            "name": "基础男性角色",
            "prompt": """图片风格为「动漫」，宫崎骏，中式古典风格
比例 「9:16」
服装要求：必须圆领袍，高领设计，严禁V领或低领，绝对不能露出脖子部位，领口要完全遮盖脖子
年龄：Youth
风格：Ancient
文化：Chinese
气质：侠义英雄，正气凛然
角度：正面半身照

单人肖像，男性，健康肌肤，黑色长发，表情严肃，中式传统服装，汉服、唐装或古代袍服，简约风格，佩戴项链，高质量角色设定图，正面视角，清晰面部特征，动漫风格"""
        },
        {
            "name": "神秘女性角色",
            "prompt": """图片风格为「动漫」，宫崎骏，中式古典风格
比例 「9:16」
服装要求：必须圆领袍，高领设计，严禁V领或低领，绝对不能露出脖子部位，领口要完全遮盖脖子
年龄：Youth
风格：Ancient
文化：Chinese
气质：神秘莫测，深不可测
角度：正面半身照

单人肖像，女性，白皙肌肤，银色中长发，表情神秘，中式传统服装，汉服、唐装或古代袍服，华丽风格，佩戴头饰，高质量角色设定图，背部视角，看不到领口和正面，动漫风格"""
        },
        {
            "name": "西式骑士",
            "prompt": """图片风格为「动漫」，宫崎骏，西式风格
比例 「9:16」
服装要求：必须圆领袍，高领设计，严禁V领或低领，绝对不能露出脖子部位，领口要完全遮盖脖子
年龄：Adult
风格：Fantasy
文化：Western
气质：骑士武士，英勇无畏
角度：正面半身照

单人肖像，男性，古铜色肌肤，金色短发，表情坚毅，西式服装，欧美风格，精致风格，佩戴手镯，高质量角色设定图，正面视角，清晰面部特征，动漫风格"""
        },
        {
            "name": "科幻战士",
            "prompt": """图片风格为「动漫」，宫崎骏，混合风格
比例 「9:16」
服装要求：必须圆领袍，高领设计，严禁V领或低领，绝对不能露出脖子部位，领口要完全遮盖脖子
年龄：Adult
风格：SciFi
文化：Western
气质：战士勇者，勇猛无敌
角度：正面半身照

单人肖像，女性，健康肌肤，红色卷发，表情冷漠，传统服装，朴素风格，无饰品，高质量角色设定图，背部视角，看不到领口和正面，动漫风格"""
        },
        {
            "name": "简化测试prompt",
            "prompt": """宫崎骏动漫风格，数字插画,高饱和度,卡通,简约画风,完整色块,整洁的画面,宫崎骏艺术风格,高饱和的色彩和柔和的阴影,童话色彩风格。 人物着装：圆领袍，高领设计，严禁V领，绝对不能露出脖子

单人肖像，男性，黑色长发，表情微笑，中式古装，正面半身照，动漫风格"""
        }
    ]
    
    return test_prompts

def generate_image_api(prompt, output_path, test_name):
    """
    调用API生成图片
    
    Args:
        prompt: 图片描述
        output_path: 输出文件路径
        test_name: 测试名称
    
    Returns:
        bool: 是否成功生成
    """
    try:
        visual_service = VisualService()
        
        # 设置访问密钥
        visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
        visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
        
        # 构建完整的prompt
        full_prompt = "以下内容为描述生成图片\n宫崎骏动漫风格，数字插画,高饱和度,卡通,简约画风,完整色块,整洁的画面,宫崎骏艺术风格,高饱和的色彩和柔和的阴影,童话色彩风格。 人物着装：圆领袍，高领设计，严禁V领，绝对不能露出脖子\n\n" + prompt + "\n\n"
        
        print(f"\n=== 测试: {test_name} ===")
        print(f"生成图片: {os.path.basename(output_path)}")
        print(f"完整prompt: {full_prompt}")
        print("-" * 80)
        
        # 请求参数
        form = {
            "req_key": "high_aes_general_v21_L",
            "prompt": full_prompt,
            "llm_seed": -1,
            "seed": -1,
            "scale": 3.5,
            "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
            "width": IMAGE_TWO_CONFIG['default_width'],
            "height": IMAGE_TWO_CONFIG['default_height'],
            "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
            "use_sr": IMAGE_TWO_CONFIG['use_sr'],
            "return_url": IMAGE_TWO_CONFIG['return_url'],
            "negative_prompt": IMAGE_TWO_CONFIG['negative_prompt'],
            "logo_info": {
                "add_logo": False,
                "position": 0,
                "language": 0,
                "opacity": 0.3,
                "logo_text_content": "这里是明水印内容"
            }
        }
        
        resp = visual_service.cv_process(form)
        
        # 检查响应
        if 'data' in resp and 'binary_data_base64' in resp['data']:
            # 获取base64图片数据
            base64_data = resp['data']['binary_data_base64'][0]
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 解码并保存图片
            image_data = base64.b64decode(base64_data)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"✓ 图片已保存: {output_path}")
            return True
        else:
            print(f"✗ 图片生成失败: {resp}")
            return False
            
    except Exception as e:
        print(f"✗ 生成图片时发生错误: {e}")
        return False

def test_single_prompt(prompt_index=None):
    """
    测试单个prompt
    
    Args:
        prompt_index: prompt索引，如果为None则显示所有可选项
    """
    test_prompts = generate_test_prompts()
    
    if prompt_index is None:
        print("可用的测试prompt:")
        for i, prompt_data in enumerate(test_prompts):
            print(f"{i + 1}. {prompt_data['name']}")
        
        try:
            choice = int(input("\n请选择要测试的prompt (输入数字): ")) - 1
            if 0 <= choice < len(test_prompts):
                prompt_index = choice
            else:
                print("无效选择")
                return
        except ValueError:
            print("请输入有效数字")
            return
    
    if 0 <= prompt_index < len(test_prompts):
        prompt_data = test_prompts[prompt_index]
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"test/test_image_output/{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成图片
        filename = f"{prompt_data['name'].replace(' ', '_')}_{timestamp}.jpeg"
        output_path = os.path.join(output_dir, filename)
        
        success = generate_image_api(prompt_data['prompt'], output_path, prompt_data['name'])
        
        if success:
            print(f"\n🎉 测试完成！图片已保存到: {output_path}")
        else:
            print(f"\n❌ 测试失败")
    else:
        print("无效的prompt索引")

def test_all_prompts():
    """
    测试所有prompt
    """
    test_prompts = generate_test_prompts()
    
    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"test/test_image_output/batch_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"开始批量测试 {len(test_prompts)} 个prompt...")
    print(f"输出目录: {output_dir}")
    
    success_count = 0
    
    for i, prompt_data in enumerate(test_prompts):
        filename = f"{i+1:02d}_{prompt_data['name'].replace(' ', '_')}_{timestamp}.jpeg"
        output_path = os.path.join(output_dir, filename)
        
        success = generate_image_api(prompt_data['prompt'], output_path, prompt_data['name'])
        
        if success:
            success_count += 1
        
        print(f"进度: {i+1}/{len(test_prompts)}")
    
    print(f"\n=== 批量测试完成 ===")
    print(f"成功生成: {success_count}/{len(test_prompts)} 张图片")
    print(f"成功率: {(success_count/len(test_prompts)*100):.1f}%")
    print(f"输出目录: {output_dir}")

def test_custom_prompt():
    """
    测试自定义prompt
    """
    print("请输入自定义prompt (输入END结束):")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        lines.append(line)
    
    custom_prompt = '\n'.join(lines)
    
    if not custom_prompt.strip():
        print("prompt不能为空")
        return
    
    # 询问生成数量
    try:
        num_images = int(input("\n请输入要生成的图片数量 (1-20，默认1): ") or "1")
        if num_images < 1 or num_images > 20:
            print("数量必须在1-20之间，使用默认值1")
            num_images = 1
    except ValueError:
        print("输入无效，使用默认值1")
        num_images = 1
    
    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"test/test_image_output/custom_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n开始生成 {num_images} 张自定义prompt图片...")
    success_count = 0
    
    # 生成图片
    for i in range(num_images):
        filename = f"custom_prompt_{i+1:02d}_{timestamp}.jpeg"
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n--- 生成第 {i+1}/{num_images} 张图片 ---")
        success = generate_image_api(custom_prompt, output_path, f"自定义prompt #{i+1}")
        
        if success:
            success_count += 1
            print(f"✓ 第 {i+1} 张图片生成成功")
        else:
            print(f"✗ 第 {i+1} 张图片生成失败")
    
    print(f"\n=== 自定义prompt测试完成 ===")
    print(f"成功生成: {success_count}/{num_images} 张图片")
    print(f"成功率: {(success_count/num_images*100):.1f}%")
    print(f"输出目录: {output_dir}")

def test_batch_same_prompt():
    """
    测试同一个prompt生成多张图片进行比较
    """
    test_prompts = generate_test_prompts()
    
    print("可用的测试prompt:")
    for i, prompt_data in enumerate(test_prompts):
        print(f"{i + 1}. {prompt_data['name']}")
    
    try:
        choice = int(input("\n请选择要测试的prompt (输入数字): ")) - 1
        if not (0 <= choice < len(test_prompts)):
            print("无效选择")
            return
    except ValueError:
        print("请输入有效数字")
        return
    
    # 询问生成数量
    try:
        num_images = int(input("\n请输入要生成的图片数量 (1-20，推荐10): "))
        if num_images < 1 or num_images > 20:
            print("数量必须在1-20之间，使用默认值10")
            num_images = 10
    except ValueError:
        print("输入无效，使用默认值10")
        num_images = 10
    
    prompt_data = test_prompts[choice]
    
    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"test/test_image_output/batch_compare_{timestamp}_{prompt_data['name'].replace(' ', '_')}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n开始批量生成 {num_images} 张图片进行比较...")
    print(f"Prompt: {prompt_data['name']}")
    print(f"输出目录: {output_dir}")
    
    success_count = 0
    
    # 生成多张图片
    for i in range(num_images):
        filename = f"{prompt_data['name'].replace(' ', '_')}_compare_{i+1:02d}_{timestamp}.jpeg"
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n--- 生成第 {i+1}/{num_images} 张图片 ---")
        success = generate_image_api(prompt_data['prompt'], output_path, f"{prompt_data['name']} 比较#{i+1}")
        
        if success:
            success_count += 1
            print(f"✓ 第 {i+1} 张图片生成成功")
        else:
            print(f"✗ 第 {i+1} 张图片生成失败")
    
    print(f"\n=== 批量比较测试完成 ===")
    print(f"成功生成: {success_count}/{num_images} 张图片")
    print(f"成功率: {(success_count/num_images*100):.1f}%")
    print(f"输出目录: {output_dir}")
    print(f"\n💡 提示: 你可以在输出目录中查看所有生成的图片，比较同一prompt的不同生成效果")

def test_custom_batch_prompt():
    """
    测试自定义prompt批量生成（专门用于比较效果）
    """
    print("=== 自定义Prompt批量生成测试 ===")
    print("此功能专门用于测试自定义prompt的生成效果一致性")
    print("\n请输入自定义prompt (输入END结束):")
    
    lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        lines.append(line)
    
    custom_prompt = '\n'.join(lines)
    
    if not custom_prompt.strip():
        print("prompt不能为空")
        return
    
    # 显示输入的prompt
    print(f"\n您输入的prompt:")
    print("-" * 50)
    print(custom_prompt)
    print("-" * 50)
    
    # 询问生成数量
    try:
        num_images = int(input("\n请输入要生成的图片数量 (1-20，推荐10): "))
        if num_images < 1 or num_images > 20:
            print("数量必须在1-20之间，使用默认值10")
            num_images = 10
    except ValueError:
        print("输入无效，使用默认值10")
        num_images = 10
    
    # 询问是否添加prompt名称
    prompt_name = input("\n请为此prompt起个名字 (可选，直接回车跳过): ").strip()
    if not prompt_name:
        prompt_name = "自定义prompt"
    
    # 创建输出目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = prompt_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    output_dir = f"test/test_image_output/custom_batch_{timestamp}_{safe_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存prompt到文件
    prompt_file = os.path.join(output_dir, "prompt.txt")
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(f"Prompt名称: {prompt_name}\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"生成数量: {num_images}\n")
        f.write(f"\nPrompt内容:\n{custom_prompt}")
    
    print(f"\n开始批量生成 {num_images} 张图片进行比较...")
    print(f"Prompt名称: {prompt_name}")
    print(f"输出目录: {output_dir}")
    
    success_count = 0
    
    # 生成多张图片
    for i in range(num_images):
        filename = f"{safe_name}_batch_{i+1:02d}_{timestamp}.jpeg"
        output_path = os.path.join(output_dir, filename)
        
        print(f"\n--- 生成第 {i+1}/{num_images} 张图片 ---")
        success = generate_image_api(custom_prompt, output_path, f"{prompt_name} 批量#{i+1}")
        
        if success:
            success_count += 1
            print(f"✓ 第 {i+1} 张图片生成成功")
        else:
            print(f"✗ 第 {i+1} 张图片生成失败")
    
    print(f"\n=== 自定义prompt批量测试完成 ===")
    print(f"成功生成: {success_count}/{num_images} 张图片")
    print(f"成功率: {(success_count/num_images*100):.1f}%")
    print(f"输出目录: {output_dir}")
    print(f"Prompt已保存到: {prompt_file}")
    print(f"\n💡 提示: 你可以在输出目录中查看所有生成的图片，比较同一自定义prompt的不同生成效果")

def main():
    """
    主函数
    """
    print("=== 图片生成Prompt测试工具 ===")
    print("基于batch_generate_character_images.py")
    print()
    
    while True:
        print("\n请选择测试模式:")
        print("1. 测试单个预设prompt")
        print("2. 测试所有预设prompt")
        print("3. 测试自定义prompt (支持批量)")
        print("4. 同一预设prompt批量生成比较 (推荐)")
        print("5. 自定义prompt专业批量测试")
        print("6. 退出")
        
        try:
            choice = input("\n请输入选择 (1-6): ").strip()
            
            if choice == '1':
                test_single_prompt()
            elif choice == '2':
                confirm = input("确认要生成所有测试图片吗？这可能需要一些时间 (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '是']:
                    test_all_prompts()
                else:
                    print("已取消批量测试")
            elif choice == '3':
                test_custom_prompt()
            elif choice == '4':
                test_batch_same_prompt()
            elif choice == '5':
                test_custom_batch_prompt()
            elif choice == '6':
                print("退出测试工具")
                break
            else:
                print("无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n用户中断，退出程序")
            break
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == '__main__':
    main()