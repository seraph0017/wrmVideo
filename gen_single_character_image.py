#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单个角色图片生成脚本
从环境变量获取参数生成单个角色的图片
"""

import os
import sys
import json
import time
import base64
import shutil
from config.config import build_character_prompt, IMAGE_TWO_CONFIG
from volcengine.visual.VisualService import VisualService

def copy_image_to_chapter_images(image_path, novel_id, chapter_id):
    """
    将生成的角色图片复制到章节的images目录
    
    Args:
        image_path (str): 原始图片路径
        novel_id (str): 小说ID
        chapter_id (str): 章节ID
    
    Returns:
        str: 复制后的图片路径，如果失败返回None
    """
    try:
        # 检查参数有效性
        if not novel_id or not chapter_id or novel_id == 'None' or chapter_id == 'None':
            print(f"无效的novel_id或chapter_id: novel_id={novel_id}, chapter_id={chapter_id}")
            return None
            
        # 构建目标images目录路径
        # 确保novel_id是3位数格式
        novel_id_formatted = f"{int(novel_id):03d}" if novel_id.isdigit() else novel_id
        chapter_images_dir = f"data/{novel_id_formatted}/{chapter_id}/images"
        
        # 确保images目录存在
        os.makedirs(chapter_images_dir, exist_ok=True)
        
        # 获取图片文件名
        image_filename = os.path.basename(image_path)
        
        # 构建目标路径
        target_path = os.path.join(chapter_images_dir, image_filename)
        
        # 复制图片
        shutil.copy2(image_path, target_path)
        
        print(f"✓ 图片已复制到: {target_path}")
        return target_path
        
    except Exception as e:
        print(f"✗ 复制图片到images目录失败: {str(e)}")
        return None

def generate_single_character_image():
    """
    从环境变量获取参数生成单个角色图片
    """
    try:
        # 从环境变量获取参数
        character_id = os.environ.get('CHARACTER_ID')
        character_name = os.environ.get('CHARACTER_NAME')
        character_gender = os.environ.get('CHARACTER_GENDER')
        character_age_group = os.environ.get('CHARACTER_AGE_GROUP')
        character_description = os.environ.get('CHARACTER_DESCRIPTION')
        image_style = os.environ.get('IMAGE_STYLE', '动漫风格')
        image_quality = os.environ.get('IMAGE_QUALITY', 'high')
        image_count = int(os.environ.get('IMAGE_COUNT', '1'))
        custom_prompt = os.environ.get('CUSTOM_PROMPT', '')
        task_id = os.environ.get('TASK_ID')
        chapter_path = os.environ.get('CHAPTER_PATH')  # 新增章节路径参数
        novel_id = os.environ.get('NOVEL_ID')  # 小说ID
        chapter_id = os.environ.get('CHAPTER_ID')  # 章节ID
        
        if not all([character_name, task_id]):
            raise ValueError("缺少必要的环境变量参数")
        
        # 如果没有提供novel_id和chapter_id，尝试从chapter_path中解析
        if not novel_id or not chapter_id:
            if chapter_path:
                # 标准化路径，处理绝对路径和相对路径
                normalized_path = os.path.normpath(chapter_path)
                # 从路径中解析，例如: data/013/chapter_002 或 /path/to/data/013/chapter_002
                path_parts = normalized_path.split(os.sep)
                
                # 查找data目录的位置
                data_index = -1
                for i, part in enumerate(path_parts):
                    if part == 'data':
                        data_index = i
                        break
                
                if data_index >= 0 and len(path_parts) > data_index + 2:
                    novel_id = path_parts[data_index + 1]
                    chapter_id = path_parts[data_index + 2]
                    print(f"从路径解析得到: novel_id={novel_id}, chapter_id={chapter_id}")
        
        print(f"开始生成角色图片: {character_name} (ID: {character_id})")
        print(f"任务ID: {task_id}")
        
        # 构建角色信息
        character_info = {
            'name': character_name,
            'gender': character_gender or '',
            'age_group': character_age_group or '',
            'description': character_description or ''
        }
        
        # 构建角色描述
        description_parts = []
        if character_info['name']:
            description_parts.append(f"角色名称: {character_info['name']}")
        if character_info['gender']:
            description_parts.append(f"性别: {character_info['gender']}")
        if character_info['age_group']:
            description_parts.append(f"年龄段: {character_info['age_group']}")
        # 构建角色描述信息
        character_desc_parts = []
        if character_info.get('face_features'):
            character_desc_parts.append(f"面部特征: {character_info['face_features']}")
        if character_info.get('body_features'):
            character_desc_parts.append(f"身材特征: {character_info['body_features']}")
        if character_info.get('hair_style'):
            character_desc_parts.append(f"发型: {character_info['hair_style']}")
        if character_info.get('hair_color'):
            character_desc_parts.append(f"发色: {character_info['hair_color']}")
        if character_info.get('special_notes'):
            character_desc_parts.append(f"特殊标记: {character_info['special_notes']}")
        
        if character_desc_parts:
            description_parts.append('; '.join(character_desc_parts))
        if custom_prompt:
            description_parts.append(f"自定义要求: {custom_prompt}")
        
        base_description = '; '.join(description_parts)
        
        # 构建提示词
        prompt = build_character_prompt(base_description)
        
        print(f"生成提示词: {prompt}")
        
        # 创建输出目录 - 放在对应的章节目录下
        output_dir = os.path.join(chapter_path, f"Character_Images/{character_name}_{character_id}")
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成图片
        success_count = 0
        failed_count = 0
        generated_images = []
        
        for i in range(image_count):
            try:
                print(f"正在生成第 {i+1}/{image_count} 张图片...")
                
                # 调用火山引擎异步API生成图片
                visual_service = VisualService()
                visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
                visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
                
                form = {
                    "req_key": IMAGE_TWO_CONFIG['req_key'],
                    "prompt": prompt,
                    "llm_seed": -1,
                    "seed": -1,
                    "scale": IMAGE_TWO_CONFIG['scale'],
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
                
                # 第一步：提交异步任务
                print(f"提交异步任务 {i+1}/{image_count}...")
                submit_resp = visual_service.cv_sync2async_submit_task(form)
                
                # 检查提交响应
                if 'data' not in submit_resp or 'task_id' not in submit_resp['data']:
                    error_msg = submit_resp.get('message', '任务提交失败')
                    print(f"✗ 任务提交失败: {error_msg}")
                    failed_count += 1
                    continue
                
                async_task_id = submit_resp['data']['task_id']
                print(f"✓ 任务提交成功，Task ID: {async_task_id}")
                
                # 第二步：轮询查询结果
                max_wait_time = 300  # 最大等待5分钟
                poll_interval = 5    # 每5秒查询一次
                waited_time = 0
                
                while waited_time < max_wait_time:
                    time.sleep(poll_interval)
                    waited_time += poll_interval
                    
                    print(f"查询任务结果... (已等待 {waited_time}s)")
                    
                    # 查询任务结果
                    query_form = {
                        "req_key": IMAGE_TWO_CONFIG['req_key'],
                        "task_id": async_task_id
                    }
                    result_resp = visual_service.cv_sync2async_get_result(query_form)
                    
                    if 'data' not in result_resp:
                        print(f"查询响应异常: {result_resp}")
                        continue
                    
                    task_status = result_resp['data'].get('status')
                    
                    if task_status == 'done':
                        # 任务完成，获取结果
                        if 'binary_data_base64' in result_resp['data']:
                            image_data = result_resp['data']['binary_data_base64'][0]
                            image_bytes = base64.b64decode(image_data)
                            
                            image_filename = f"{character_name}.png"
                            image_path = os.path.join(output_dir, image_filename)
                            
                            with open(image_path, 'wb') as f:
                                f.write(image_bytes)
                            
                            # 复制图片到章节images目录
                            copied_path = copy_image_to_chapter_images(image_path, novel_id, chapter_id)
                            
                            generated_images.append({
                                'filename': image_filename,
                                'path': image_path,
                                'copied_path': copied_path,
                                'size': len(image_bytes),
                                'task_id': async_task_id
                            })
                            
                            success_count += 1
                            print(f"✓ 图片生成成功: {image_path}")
                            break
                        else:
                            print(f"✗ 任务完成但没有图片数据")
                            failed_count += 1
                            break
                    elif task_status == 'failed':
                        error_msg = result_resp['data'].get('message', '任务执行失败')
                        print(f"✗ 任务执行失败: {error_msg}")
                        failed_count += 1
                        break
                    elif task_status in ['pending', 'running', 'in_queue']:
                        print(f"任务状态: {task_status}，继续等待...")
                        continue
                    else:
                        print(f"未知任务状态: {task_status}，继续等待...")
                        continue
                else:
                    # 超时
                    print(f"✗ 任务超时 (等待了 {max_wait_time}s)")
                    failed_count += 1
                
                # 添加延迟避免API限制
                if i < image_count - 1:
                    time.sleep(2)
                    
            except Exception as e:
                print(f"✗ 第 {i+1} 张图片生成失败: {str(e)}")
                failed_count += 1
                continue
        
        # 生成结果报告
        result = {
            'task_id': task_id,
            'character_id': character_id,
            'character_name': character_name,
            'total_requested': image_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'output_directory': output_dir,
            'generated_images': generated_images,
            'prompt_used': prompt
        }
        
        # 保存结果到JSON文件
        result_file = os.path.join(output_dir, f"generation_result_{task_id}.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 生成完成 ===")
        print(f"成功: {success_count}/{image_count}")
        print(f"失败: {failed_count}/{image_count}")
        print(f"输出目录: {output_dir}")
        print(f"结果文件: {result_file}")
        
        # 返回结果给调用者
        if success_count > 0:
            # 输出JSON格式的结果供Web系统解析
            result = {
                "status": "success",
                "generated_images": [img.get('copied_path', img['path']) for img in generated_images if img.get('copied_path')],
                "success_count": success_count,
                "failed_count": failed_count,
                "character_name": character_name,
                "task_id": task_id
            }
            print(json.dumps(result, ensure_ascii=False))
            print("角色图片生成任务完成")
            return True
        else:
            result = {
                "status": "failed",
                "generated_images": [],
                "success_count": success_count,
                "failed_count": failed_count,
                "character_name": character_name,
                "task_id": task_id
            }
            print(json.dumps(result, ensure_ascii=False))
            print("角色图片生成任务失败")
            return False
            
    except Exception as e:
        print(f"角色图片生成异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主函数：支持命令行参数和环境变量两种调用方式
    
    命令行调用:
    python gen_single_character_image.py <characters_json_path> <character_name> <image_count>
    
    环境变量调用（Web系统使用）:
    设置环境变量后直接调用: python gen_single_character_image.py
    """
    # 检查是否有足够的命令行参数
    if len(sys.argv) >= 4:
        # 命令行模式
        characters_json_path = sys.argv[1]
        character_name = sys.argv[2]
        image_count = int(sys.argv[3])
        
        # 读取角色信息
        try:
            with open(characters_json_path, 'r', encoding='utf-8') as f:
                characters_data = json.load(f)
        except Exception as e:
            print(f"读取角色文件失败: {e}")
            sys.exit(1)
        
        # 查找指定角色
        character_info = None
        for char in characters_data.get('characters', []):
            if char.get('name') == character_name:
                character_info = char
                break
        
        if not character_info:
            print(f"未找到角色: {character_name}")
            sys.exit(1)
        
        # 设置环境变量
        os.environ['CHARACTER_ID'] = str(character_info.get('id', '1'))
        os.environ['CHARACTER_NAME'] = character_info.get('name', '')
        os.environ['CHARACTER_GENDER'] = character_info.get('gender', '')
        os.environ['CHARACTER_AGE_GROUP'] = character_info.get('age_group', '')
        os.environ['CHARACTER_DESCRIPTION'] = character_info.get('description', '')
        os.environ['IMAGE_COUNT'] = str(image_count)
        os.environ['TASK_ID'] = f"manual_{character_name}_{int(time.time())}"
        os.environ['CHAPTER_PATH'] = os.path.dirname(os.path.abspath(characters_json_path))
        
    else:
        # 环境变量模式（Web系统调用）
        # 检查必要的环境变量是否存在
        required_env_vars = ['CHARACTER_NAME', 'TASK_ID', 'CHAPTER_PATH']
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"环境变量模式缺少必要参数: {', '.join(missing_vars)}")
            print("命令行模式用法: python gen_single_character_image.py <characters_json_path> <character_name> <image_count>")
            print("示例: python gen_single_character_image.py data/013/chapter_002/characters.json 钱守郁 1")
            sys.exit(1)
        
        print(f"环境变量模式: 角色={os.environ.get('CHARACTER_NAME')}, 任务ID={os.environ.get('TASK_ID')}")
    
    # 调用生成函数
    success = generate_single_character_image()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()