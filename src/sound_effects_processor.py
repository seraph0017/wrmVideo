#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音效处理模块
基于字幕内容和时间戳添加音效
"""

import os
import re
import glob
import random
import ffmpeg
from pathlib import Path

class SoundEffectsProcessor:
    def __init__(self, sound_effects_dir):
        """
        初始化音效处理器
        
        Args:
            sound_effects_dir: 音效文件目录路径
        """
        self.sound_effects_dir = sound_effects_dir
        self.sound_effects_map = self._load_sound_effects()
        
        # 关键词映射到音效搜索关键词（用于文件名匹配）
        self.keyword_mapping = {
            # 动物音效
            '狗': ['狗', 'dog', '犬'],
            '猫': ['猫', 'cat'],
            '鸟': ['鸟', 'bird'],
            '马': ['马', 'horse'],
            '狼': ['狼', 'wolf'],
            '虎': ['虎', 'tiger'],
            '象': ['象', 'elephant'],
            '鸡': ['鸡', 'chicken'],
            '羊': ['羊', 'sheep'],
            '牛': ['牛', 'cow'],
            
            # 动作音效
            '脚步': ['脚步', 'footstep', '走'],
            '跑': ['跑', 'run', '奔跑'],
            '开门': ['开门', 'door', '门'],
            '关门': ['关门', 'door', '门'],
            '打击': ['打击', 'hit', '打', '击'],
            '爆炸': ['爆炸', 'explosion', '爆破'],
            '水': ['水', 'water', '流水'],
            '风': ['风', 'wind'],
            '雷': ['雷', 'thunder'],
            '雨': ['雨', 'rain'],
            
            # 交通工具
            '车': ['车', 'car', '汽车'],
            '飞机': ['飞机', 'plane', 'aircraft'],
            
            # 电子设备
            '电话': ['电话', 'phone', '铃声'],
            '电脑': ['电脑', 'computer'],
            '打字': ['打字', 'typing', '键盘'],
            
            # 环境音效
            '人群': ['人群', 'crowd', '嘈杂'],
            '嘈杂': ['嘈杂', 'noise', '喧闹'],
            '喧闹': ['喧闹', 'noise', '嘈杂'],
            '议论': ['议论', 'talk', '说话'],
        }
    
    def _load_sound_effects(self):
        """
        递归加载所有可用的音效文件
        
        Returns:
            dict: 文件名到完整路径的映射字典
        """
        sound_effects = {}
        
        if not os.path.exists(self.sound_effects_dir):
            print(f"音效目录不存在: {self.sound_effects_dir}")
            return sound_effects
        
        # 递归搜索所有音频文件
        audio_extensions = ['.mp3', '.wav', '.WAV', '.ogg', '.m4a', '.flac', '.aac']
        
        for root, dirs, files in os.walk(self.sound_effects_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in [ext.lower() for ext in audio_extensions]:
                    # 使用文件名（不含扩展名）作为键
                    file_name = os.path.splitext(file)[0]
                    sound_effects[file_name.lower()] = file_path
                    
                    # 同时使用完整文件名作为键
                    sound_effects[file.lower()] = file_path
                    
        print(f"从 {self.sound_effects_dir} 加载了 {len(sound_effects)} 个音效文件")
        return sound_effects
    
    def parse_ass_file(self, ass_file_path):
        """
        解析ASS字幕文件，提取对话内容和时间戳
        
        Args:
            ass_file_path: ASS文件路径
            
        Returns:
            list: 包含时间戳和文本的字典列表
        """
        dialogues = []
        
        try:
            with open(ass_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找对话行
            dialogue_pattern = r'Dialogue: \d+,([^,]+),([^,]+),[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,(.+)'
            matches = re.findall(dialogue_pattern, content)
            
            for match in matches:
                start_time, end_time, text = match
                # 清理文本，移除ASS格式标签
                clean_text = re.sub(r'\{[^}]*\}', '', text).strip()
                
                dialogues.append({
                    'start_time': start_time.strip(),
                    'end_time': end_time.strip(), 
                    'text': clean_text,
                    'start_seconds': self._parse_ass_time(start_time.strip()),
                    'end_seconds': self._parse_ass_time(end_time.strip())
                })
                
        except Exception as e:
            print(f"解析ASS文件失败: {e}")
            
        return dialogues
    
    def _parse_ass_time(self, time_str):
        """
        解析ASS时间格式为秒数
        
        Args:
            time_str: ASS时间字符串 (H:MM:SS.CC)
            
        Returns:
            float: 秒数
        """
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds_parts = parts[2].split('.')
            seconds = int(seconds_parts[0])
            centiseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100.0
            return total_seconds
        except Exception as e:
            print(f"解析时间失败: {time_str}, 错误: {e}")
            return 0.0
    
    def match_sound_effects(self, dialogues):
        """
        根据对话内容智能匹配音效，确保前十秒内每五秒至少有一个音效
        
        Args:
            dialogues: 对话列表
            
        Returns:
            list: 音效事件列表
        """
        sound_events = []
        
        # 首先进行常规的台词音效匹配
        for dialogue in dialogues:
            text = dialogue['text']
            matched_file = None
            matched_keyword = None
            
            # 检查关键词映射
            for keyword, search_terms in self.keyword_mapping.items():
                if keyword in text:
                    # 在音效文件中搜索匹配的文件
                    candidate_files = []
                    
                    for search_term in search_terms:
                        for file_key, file_path in self.sound_effects_map.items():
                            if search_term.lower() in file_key.lower():
                                candidate_files.append(file_path)
                    
                    # 如果找到候选文件，随机选择一个
                    if candidate_files:
                        matched_file = random.choice(candidate_files)
                        matched_keyword = keyword
                        break
            
            # 如果通过关键词映射没有找到，尝试直接文字匹配
            if not matched_file:
                # 提取文本中的关键词进行直接匹配
                text_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
                
                for word in text_words:
                    if len(word) >= 2:  # 只考虑长度>=2的词
                        candidate_files = []
                        for file_key, file_path in self.sound_effects_map.items():
                            if word.lower() in file_key.lower():
                                candidate_files.append(file_path)
                        
                        if candidate_files:
                            matched_file = random.choice(candidate_files)
                            matched_keyword = word
                            break
            
            # 如果找到匹配的音效文件，添加到事件列表
            if matched_file:
                # 为重复使用的音效添加音量随机变化，避免完全相同的处理
                base_volume = 0.3
                volume_variation = random.uniform(-0.1, 0.1)  # ±0.1的音量变化
                final_volume = max(0.1, min(0.5, base_volume + volume_variation))
                
                sound_events.append({
                    'start_time': dialogue['start_seconds'],
                    'end_time': dialogue['end_seconds'],
                    'sound_file': matched_file,
                    'volume': final_volume,
                    'keyword': matched_keyword,
                    'text': text
                })
                print(f"匹配音效: {matched_keyword} -> {os.path.basename(matched_file)} (时间: {dialogue['start_seconds']:.2f}s, 音量: {final_volume:.2f})")
        
        # 确保前十秒内每五秒至少有一个音效
        sound_events = self._ensure_early_sound_effects(sound_events, dialogues)
        
        return sound_events
    
    def filter_overlapping_effects(self, sound_events):
        """
        过滤重叠的音效事件，避免在音效持续时间内重复添加相同音效
        
        Args:
            sound_events: 原始音效事件列表
            
        Returns:
            list: 过滤后的音效事件列表
        """
        if not sound_events:
            return sound_events
        
        # 为每个音效事件添加默认持续时间
        for event in sound_events:
            if 'duration' not in event:
                # 根据音效类型设置默认持续时间
                if '雷' in event.get('keyword', ''):
                    event['duration'] = 3.0  # 雷声持续3秒
                elif '风' in event.get('keyword', ''):
                    event['duration'] = 4.0  # 风声持续4秒
                elif '马' in event.get('keyword', ''):
                    event['duration'] = 2.5  # 马蹄声持续2.5秒
                elif '场景音效' in event.get('keyword', ''):
                    event['duration'] = 5.0  # 场景音效持续5秒
                else:
                    event['duration'] = 2.0  # 默认持续2秒
            
            event['end_time'] = event['start_time'] + event['duration']
        
        # 按开始时间排序
        sound_events.sort(key=lambda x: x['start_time'])
        
        # 按音效文件分组，避免同一音效文件的重叠
        filtered_events = []
        file_last_end_time = {}  # 记录每个音效文件的最后结束时间
        
        for event in sound_events:
            sound_file = event['sound_file']
            start_time = event['start_time']
            
            # 检查是否与同一音效文件的前一个事件重叠
            if sound_file in file_last_end_time:
                last_end_time = file_last_end_time[sound_file]
                if start_time < last_end_time:
                    # 重叠，跳过这个事件
                    print(f"跳过重叠音效: {os.path.basename(sound_file)} 在 {start_time:.2f}s (与 {last_end_time:.2f}s 结束的音效重叠)")
                    continue
            
            # 添加到过滤后的列表
            filtered_events.append(event)
            file_last_end_time[sound_file] = event['end_time']
        
        return filtered_events
    
    def _ensure_early_sound_effects(self, sound_events, dialogues):
        """
        确保前十秒内每五秒至少有一个音效
        
        Args:
            sound_events: 现有音效事件列表
            dialogues: 对话列表
            
        Returns:
            list: 补充后的音效事件列表
        """
        # 检查前十秒内的音效分布
        early_intervals = [(0, 5), (5, 10)]  # 两个五秒区间
        
        for start_time, end_time in early_intervals:
            # 检查该区间是否已有音效
            has_sound_in_interval = any(
                start_time <= event['start_time'] < end_time 
                for event in sound_events
            )
            
            if not has_sound_in_interval:
                print(f"前{end_time}秒内缺少音效，添加场景音效")
                
                # 在该区间内寻找台词，优先在台词时间添加音效
                interval_dialogues = [
                    d for d in dialogues 
                    if start_time <= d['start_seconds'] < end_time
                ]
                
                if interval_dialogues:
                    # 选择该区间内的第一个台词时间点
                    target_dialogue = interval_dialogues[0]
                    target_time = target_dialogue['start_seconds']
                    context_text = target_dialogue['text']
                else:
                    # 如果该区间没有台词，在区间中点添加音效
                    target_time = (start_time + end_time) / 2
                    context_text = "场景"
                
                # 选择合适的场景音效
                scene_sound = self._get_scene_sound_effect(context_text)
                
                if scene_sound:
                    sound_events.append({
                        'start_time': target_time,
                        'end_time': target_time + 2.0,  # 默认2秒时长
                        'sound_file': scene_sound,
                        'volume': 0.2,  # 场景音效音量稍低
                        'keyword': '场景音效',
                        'text': f'自动添加的场景音效 ({start_time}-{end_time}s区间)'
                    })
                    print(f"在 {target_time:.2f}s 添加场景音效: {os.path.basename(scene_sound)}")
        
        # 按时间排序
        sound_events.sort(key=lambda x: x['start_time'])
        return sound_events
    
    def _get_scene_sound_effect(self, context_text):
        """
        根据上下文选择合适的场景音效
        
        Args:
            context_text: 上下文文本
            
        Returns:
            str: 音效文件路径，如果没有找到则返回None
        """
        # 定义场景音效优先级列表
        scene_keywords = [
            # 古代/宫廷场景
            ['古', '宫', '殿', '朝', '廷', '皇', '帝', '王', '太子'],
            # 自然场景
            ['风', '雨', '雷', '水', '山', '林', '鸟', '虫'],
            # 战斗场景
            ['战', '斗', '剑', '刀', '兵', '军', '打', '击'],
            # 日常场景
            ['门', '步', '走', '来', '去', '声', '响']
        ]
        
        # 根据上下文文本匹配场景类型
        for keywords in scene_keywords:
            for keyword in keywords:
                if keyword in context_text:
                    # 寻找相关的音效文件
                    candidate_files = []
                    for file_key, file_path in self.sound_effects_map.items():
                        if keyword in file_key or any(k in file_key for k in keywords):
                            candidate_files.append(file_path)
                    
                    if candidate_files:
                        return random.choice(candidate_files)
        
        # 如果没有匹配到特定场景，优先使用脚步声作为默认音效
        footstep_sounds = []
        footstep_keywords = ['脚步', 'footstep', '走', 'walk', 'step']
        
        for keyword in footstep_keywords:
            for file_key, file_path in self.sound_effects_map.items():
                if keyword.lower() in file_key.lower():
                    footstep_sounds.append(file_path)
        
        if footstep_sounds:
            print(f"使用默认脚步声音效: {os.path.basename(random.choice(footstep_sounds))}")
            return random.choice(footstep_sounds)
        
        # 如果没有脚步声，使用通用的环境音效
        generic_sounds = []
        generic_keywords = ['环境', 'ambient', '背景', 'background', '风', 'wind', '自然', 'nature']
        
        for keyword in generic_keywords:
            for file_key, file_path in self.sound_effects_map.items():
                if keyword.lower() in file_key.lower():
                    generic_sounds.append(file_path)
        
        if generic_sounds:
            return random.choice(generic_sounds)
        
        # 最后的备选：随机选择任意音效文件
        if self.sound_effects_map:
            return random.choice(list(self.sound_effects_map.values()))
        
        return None
    
    def create_sound_effects_audio(self, sound_events, total_duration, output_path):
        """
        创建包含所有音效的音频轨道
        
        Args:
            sound_events: 音效事件列表
            total_duration: 总时长
            output_path: 输出音频路径
            
        Returns:
            bool: 是否成功
        """
        if not sound_events:
            print("没有音效事件，跳过音效轨道创建")
            return False
            
        # 初始化临时文件列表
        temp_effect_files = []
        
        try:
            # 创建静音基础轨道
            base_audio = ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=48000', 
                                    f='lavfi', t=total_duration)
            
            # 准备所有音效输入
            audio_inputs = [base_audio]
            
            # 使用分步处理避免FFmpeg过滤器图冲突
            # 为每个音效创建独立的临时文件，然后再混合
            temp_dir = os.path.dirname(output_path)
            
            for i, event in enumerate(sound_events):
                try:
                    sound_file = event['sound_file']
                    temp_effect_file = os.path.join(temp_dir, f"temp_effect_{i}.mp3")
                    
                    # 为每个音效创建独立的处理流程
                    sound_input = ffmpeg.input(sound_file)
                    
                    # 调整音量并添加延迟
                    if event['start_time'] > 0:
                        # 先添加延迟，再调整音量
                        sound_delayed = sound_input.filter('adelay', delays=f"{int(event['start_time'] * 1000)}")
                        sound_volume = sound_delayed.filter('volume', volume=event['volume'])
                    else:
                        sound_volume = sound_input.filter('volume', volume=event['volume'])
                    
                    # 输出到临时文件
                    (
                        ffmpeg
                        .output(sound_volume, temp_effect_file, acodec='mp3', audio_bitrate='128k', t=total_duration)
                        .overwrite_output()
                        .run(quiet=True)
                    )
                    
                    temp_effect_files.append(temp_effect_file)
                    print(f"处理音效 {i+1}/{len(sound_events)}: {os.path.basename(sound_file)}")
                    
                except Exception as e:
                    print(f"处理音效失败: {event['sound_file']}, 错误: {e}")
            
            # 将所有临时音效文件添加到混合列表
            for temp_file in temp_effect_files:
                if os.path.exists(temp_file):
                    audio_inputs.append(ffmpeg.input(temp_file))
            
            # 混合所有音频
            if len(audio_inputs) > 1:
                mixed_audio = ffmpeg.filter(audio_inputs, 'amix', 
                                          inputs=len(audio_inputs), 
                                          duration='longest')
            else:
                mixed_audio = audio_inputs[0]
            
            # 输出音效轨道
            (
                ffmpeg
                .output(mixed_audio, output_path, acodec='mp3', audio_bitrate='128k')
                .overwrite_output()
                .run()
            )
            
            print(f"音效轨道创建成功: {output_path}")
            
            # 清理临时文件
            for temp_file in temp_effect_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"创建音效轨道失败: {e}")
            
            # 清理临时文件
            try:
                for temp_file in temp_effect_files:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            except:
                pass
            
            return False
    
    def process_chapter_sound_effects(self, ass_file_path, total_duration, output_path):
        """
        处理单个章节的音效
        
        Args:
            ass_file_path: ASS字幕文件路径
            total_duration: 视频总时长
            output_path: 输出音效轨道路径
            
        Returns:
            bool: 是否成功创建音效轨道
        """
        print(f"开始处理章节音效: {ass_file_path}")
        
        # 解析字幕文件
        dialogues = self.parse_ass_file(ass_file_path)
        if not dialogues:
            print("未找到有效对话，跳过音效处理")
            return False
        
        print(f"解析到 {len(dialogues)} 条对话")
        
        # 匹配音效
        sound_events = self.match_sound_effects(dialogues)
        if not sound_events:
            print("未匹配到任何音效")
            return False
        
        print(f"匹配到 {len(sound_events)} 个音效事件")
        
        # 创建音效轨道
        return self.create_sound_effects_audio(sound_events, total_duration, output_path)