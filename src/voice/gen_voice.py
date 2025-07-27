#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音生成模块
使用配置化的TTS参数
"""

import os
import sys
import requests
import json
import uuid
import base64
from typing import Optional, Dict, Any

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from config.prompt_config import prompt_config, VOICE_PRESETS, validate_voice_preset
from config.config import TTS_CONFIG

class VoiceGenerator:
    """
    语音生成器类
    """
    
    def __init__(self, tts_config: Optional[Dict] = None):
        """
        初始化语音生成器
        
        Args:
            tts_config: TTS配置，如果为None则使用默认配置
        """
        self.tts_config = tts_config or TTS_CONFIG
        self.api_url = "https://openspeech.bytedance.com/api/v1/tts"
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        清理文本，移除可能导致TTS问题的字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        import re
        
        # 先保护人名标记中的 & 符号（如 &芜音&、&谭辞& 等）
        # 将人名标记临时替换为占位符
        name_pattern = r'&([^&\s]+)&'
        name_matches = re.findall(name_pattern, text)
        
        # 用占位符替换人名标记
        cleaned_text = text
        for i, name in enumerate(name_matches):
            placeholder = f'__NAME_PLACEHOLDER_{i}__'
            cleaned_text = cleaned_text.replace(f'&{name}&', placeholder, 1)
        
        # 现在可以安全地移除剩余的 & 符号
        cleaned_text = cleaned_text.replace('&', '')
        
        # 恢复人名标记，但移除 & 符号，只保留人名
        for i, name in enumerate(name_matches):
            placeholder = f'__NAME_PLACEHOLDER_{i}__'
            cleaned_text = cleaned_text.replace(placeholder, name)
        
        # 可以根据需要添加更多清理规则
        # cleaned_text = cleaned_text.replace('...', '。')
        
        return cleaned_text
    
    def generate_voice(self, text: str, output_path: str, 
                      preset: str = 'default', **kwargs) -> bool:
        """
        生成语音文件
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            preset: 语音预设，可选值见VOICE_PRESETS
            **kwargs: 其他参数
        
        Returns:
            bool: 是否生成成功
        """
        
        # 验证预设
        if not validate_voice_preset(preset):
            print(f"错误：不支持的语音预设 '{preset}'")
            print(f"可用预设：{list(VOICE_PRESETS.keys())}")
            return False
        
        try:
            # 清理文本
            cleaned_text = self._clean_text_for_tts(text)
            
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 获取预设参数
            preset_params = VOICE_PRESETS[preset].copy()
            preset_params.update(kwargs)  # 允许覆盖预设参数
            
            # 使用配置管理器生成请求配置
            request_config = prompt_config.get_voice_config(
                text=cleaned_text,
                request_id=request_id,
                tts_config=self.tts_config,
                **preset_params
            )
            
            print(f"使用语音预设：{preset}")
            print(f"请求ID：{request_id}")
            print(f"原始文本长度：{len(text)} 字符")
            print(f"清理后文本长度：{len(cleaned_text)} 字符")
            if text != cleaned_text:
                print("文本已清理，移除了可能导致问题的字符")
            
            # 发送请求
            headers = {
                'Authorization': f'Bearer; {self.tts_config["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            print("正在生成语音...")
            print(request_config)
            response = requests.post(
                self.api_url,
                headers=headers,
                json=request_config,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    # 解析JSON响应
                    resp_json = response.json()
                    print(f"响应状态: {resp_json}")
                    
                    # 检查响应是否包含音频数据
                    if "data" in resp_json and resp_json.get("code") == 3000:
                        # 提取base64编码的音频数据
                        audio_data = resp_json["data"]
                        
                        # 解码并保存音频文件
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(base64.b64decode(audio_data))
                        
                        print(f"语音文件已生成：{output_path}")
                        return True
                    else:
                        print(f"API响应错误：{resp_json.get('message', '未知错误')}")
                        print(f"错误代码：{resp_json.get('code', 'N/A')}")
                        return False
                        
                except json.JSONDecodeError:
                    print("响应不是有效的JSON格式")
                    print(f"原始响应：{response.text[:500]}...")
                    return False
                except Exception as e:
                    print(f"处理响应时出错：{e}")
                    return False
            else:
                print(f"API请求失败，状态码：{response.status_code}")
                print(f"响应内容：{response.text}")
                return False
                
        except Exception as e:
            print(f"生成语音时出错：{e}")
            return False
    
    def generate_voice_with_timestamps(self, text: str, output_path: str, 
                                     preset: str = 'default', **kwargs) -> Dict[str, Any]:
        """
        生成语音文件并返回包含时间戳信息的完整结果
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            preset: 语音预设，可选值见VOICE_PRESETS
            **kwargs: 其他参数
        
        Returns:
            Dict[str, Any]: 包含生成结果和API响应的字典
                {
                    'success': bool,  # 是否生成成功
                    'output_path': str,  # 输出文件路径
                    'api_response': dict,  # 完整的API响应
                    'error_message': str  # 错误信息（如果有）
                }
        """
        result = {
            'success': False,
            'output_path': output_path,
            'api_response': None,
            'error_message': None
        }
        
        # 验证预设
        if not validate_voice_preset(preset):
            result['error_message'] = f"不支持的语音预设 '{preset}'"
            return result
        
        try:
            # 清理文本
            cleaned_text = self._clean_text_for_tts(text)
            
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 获取预设参数
            preset_params = VOICE_PRESETS[preset].copy()
            preset_params.update(kwargs)  # 允许覆盖预设参数
            
            # 使用配置管理器生成请求配置
            request_config = prompt_config.get_voice_config(
                text=cleaned_text,
                request_id=request_id,
                tts_config=self.tts_config,
                **preset_params
            )
            
            print(f"使用语音预设：{preset}")
            print(f"请求ID：{request_id}")
            print(f"原始文本长度：{len(text)} 字符")
            print(f"清理后文本长度：{len(cleaned_text)} 字符")
            if text != cleaned_text:
                print("文本已清理，移除了可能导致问题的字符")
            
            # 发送请求
            headers = {
                'Authorization': f'Bearer; {self.tts_config["access_token"]}',
                'Content-Type': 'application/json'
            }
            
            print("正在生成语音...")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=request_config,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    # 解析JSON响应
                    resp_json = response.json()
                    result['api_response'] = resp_json
                    print(f"响应状态: {resp_json}")
                    
                    # 检查响应是否包含音频数据
                    if "data" in resp_json and resp_json.get("code") == 3000:
                        # 提取base64编码的音频数据
                        audio_data = resp_json["data"]
                        
                        # 解码并保存音频文件
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(base64.b64decode(audio_data))
                        
                        print(f"语音文件已生成：{output_path}")
                        result['success'] = True
                        return result
                    else:
                        error_msg = f"API响应错误：{resp_json.get('message', '未知错误')}"
                        result['error_message'] = error_msg
                        print(error_msg)
                        print(f"错误代码：{resp_json.get('code', 'N/A')}")
                        return result
                        
                except json.JSONDecodeError:
                    result['error_message'] = "响应不是有效的JSON格式"
                    print(result['error_message'])
                    print(f"原始响应：{response.text[:500]}...")
                    return result
                except Exception as e:
                    result['error_message'] = f"处理响应时出错：{e}"
                    print(result['error_message'])
                    return result
            else:
                result['error_message'] = f"API请求失败，状态码：{response.status_code}"
                print(result['error_message'])
                print(f"响应内容：{response.text}")
                return result
                
        except Exception as e:
            result['error_message'] = f"生成语音时出错：{e}"
            print(result['error_message'])
            return result
    
    def generate_voice_batch(self, text_list: list, output_dir: str, 
                           preset: str = 'default', **kwargs) -> Dict[str, bool]:
        """
        批量生成语音文件
        
        Args:
            text_list: 文本列表
            output_dir: 输出目录
            preset: 语音预设
            **kwargs: 其他参数
        
        Returns:
            Dict[str, bool]: 每个文件的生成结果
        """
        results = {}
        
        for i, text in enumerate(text_list):
            output_path = os.path.join(output_dir, f"voice_{i+1:03d}.mp3")
            success = self.generate_voice(text, output_path, preset, **kwargs)
            results[output_path] = success
            
            if success:
                print(f"✓ 第 {i+1}/{len(text_list)} 个语音文件生成成功")
            else:
                print(f"✗ 第 {i+1}/{len(text_list)} 个语音文件生成失败")
        
        return results

def list_available_presets():
    """
    列出所有可用的语音预设
    """
    print("可用的语音预设：")
    for preset_key, preset_config in VOICE_PRESETS.items():
        print(f"  {preset_key}:")
        for param, value in preset_config.items():
            print(f"    {param}: {value}")
        print()

def main():
    """
    主函数，用于测试
    """
    print("语音生成模块测试")
    print("=" * 50)
    
    # 列出可用预设
    list_available_presets()
    
    # 创建语音生成器
    generator = VoiceGenerator()
    
    # 测试文本
    test_text = "这是一个测试文本，用于验证语音生成功能是否正常工作。"
    
    # 测试不同预设
    for preset in ['default', 'slow', 'fast']:
        print(f"\n测试预设：{preset}")
        print("-" * 30)
        output_path = f"test_voice_{preset}.mp3"
        generator.generate_voice(test_text, output_path, preset)

if __name__ == "__main__":
    main()