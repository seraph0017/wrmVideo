import json
from gen_ass import calculate_segment_timestamps, split_text_naturally

# 加载数据
with open('/Users/nathan/Projects/wrmVideo/data/005/chapter_001/chapter_001_narration_01_timestamps.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

original_text = data['text']
character_timestamps = data['character_timestamps']

# 分割文本
segments = split_text_naturally(original_text)

print(f"原始文本: {original_text}")
print(f"字符时间戳数量: {len(character_timestamps)}")
print(f"原始文本长度: {len(original_text)}")

# 检查所有段落
print("\n所有段落:")
for i, seg in enumerate(segments):
    print(f"{i+1}. '{seg}'")

# 测试第15段（"我以后怕是看不到了"）
segment_15 = segments[14]  # 第15段（索引14）
print(f"\n第15段: '{segment_15}'")
clean_segment_15 = segment_15.strip().replace(' ', '').replace('"', '')
print(f"清理后: '{clean_segment_15}'")

# 测试完整函数处理第15段
print(f"\n=== 测试完整函数处理第15段 ===")
segment_timestamps = calculate_segment_timestamps([segment_15], character_timestamps, original_text)
print(f"返回的段落数: {len(segment_timestamps)}")
if segment_timestamps:
    for i, seg in enumerate(segment_timestamps):
        print(f"{i+1}. {seg['text']} ({seg['start_time']:.3f}s - {seg['end_time']:.3f}s)")
else:
    print("没有返回任何段落")

# 测试完整函数处理所有段落
print(f"\n=== 测试完整函数处理所有段落 ===")
all_segment_timestamps = calculate_segment_timestamps(segments, character_timestamps, original_text)
print(f"返回的段落数: {len(all_segment_timestamps)}")
for i, seg in enumerate(all_segment_timestamps):
    print(f"{i+1}. {seg['text']} ({seg['start_time']:.3f}s - {seg['end_time']:.3f}s)")