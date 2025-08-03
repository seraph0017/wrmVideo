import json
from gen_ass import split_text_naturally

# 加载数据
with open('/Users/nathan/Projects/wrmVideo/data/005/chapter_001/chapter_001_narration_01_timestamps.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

original_text = data['text']
character_timestamps = data['character_timestamps']

# 分割文本
segments = split_text_naturally(original_text)

print(f"原始文本: {original_text}")
print(f"字符时间戳数量: {len(character_timestamps)}")

# 手动模拟calculate_segment_timestamps的逻辑
current_original_pos = 0

for segment_idx, segment in enumerate(segments):
    print(f"\n=== 处理段落 {segment_idx + 1}: '{segment}' ===")
    print(f"当前位置: {current_original_pos}")
    
    if current_original_pos >= len(character_timestamps):
        print(f"跳过: 已超出字符时间戳范围")
        break
    
    # 清理段落文本
    clean_segment = segment.strip().replace(' ', '').replace('"', '')
    print(f"清理后: '{clean_segment}'")
    
    if not clean_segment:
        print(f"跳过: 空段落")
        continue
    
    # 查找匹配位置
    segment_start_pos = -1
    segment_end_pos = -1
    segment_char_index = 0
    
    for i in range(current_original_pos, len(original_text)):
        char = original_text[i]
        
        # 跳过标点符号
        if char in '，。！？；：、"':
            continue
            
        # 匹配段落字符
        if segment_char_index < len(clean_segment) and char == clean_segment[segment_char_index]:
            if segment_char_index == 0:
                segment_start_pos = i
                print(f"找到开始位置: {i} (字符: '{char}')")
            segment_char_index += 1
            
            # 如果匹配完整个段落
            if segment_char_index == len(clean_segment):
                segment_end_pos = i
                print(f"找到结束位置: {i} (字符: '{char}')")
                break
        elif segment_char_index > 0:
            # 如果已经开始匹配但失败了
            segment_char_index = 0
            segment_start_pos = -1
            # 重新检查当前字符
            if char == clean_segment[0]:
                segment_start_pos = i
                segment_char_index = 1
                print(f"重新开始匹配: {i} (字符: '{char}')")
    
    if segment_start_pos == -1 or segment_char_index < len(clean_segment):
        print(f"警告: 无法找到段落 '{clean_segment}' 的匹配位置")
        print(f"segment_start_pos: {segment_start_pos}")
        print(f"segment_char_index: {segment_char_index}/{len(clean_segment)}")
        continue
    
    print(f"成功匹配: 位置 {segment_start_pos} - {segment_end_pos}")
    
    # 获取时间戳
    print(f"检查时间戳条件:")
    print(f"  segment_start_pos ({segment_start_pos}) < len(character_timestamps) ({len(character_timestamps)}): {segment_start_pos < len(character_timestamps)}")
    print(f"  segment_end_pos ({segment_end_pos}) < len(character_timestamps) ({len(character_timestamps)}): {segment_end_pos < len(character_timestamps)}")
    
    if (segment_start_pos < len(character_timestamps) and 
        segment_end_pos < len(character_timestamps)):
        
        start_time = character_timestamps[segment_start_pos]['start_time']
        end_time = character_timestamps[segment_end_pos]['end_time']
        
        print(f"时间戳: {start_time:.3f}s - {end_time:.3f}s")
    else:
        print(f"无法获取时间戳 - 索引超出范围")
    
    # 更新当前位置
    current_original_pos = segment_end_pos + 1
    print(f"更新当前位置到: {current_original_pos}")
    
    # 显示接下来几个字符
    if current_original_pos < len(original_text):
        next_chars = original_text[current_original_pos:current_original_pos+10]
        print(f"接下来的字符: '{next_chars}'")