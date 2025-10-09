#!/usr/bin/env python3
"""
验证所有章节的scene文件生成数量是否正确
"""

import os
import re
from pathlib import Path

def count_scenes_in_narration(narration_file):
    """
    统计narration.txt文件中的分镜数量
    """
    try:
        with open(narration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有分镜标签
        scene_pattern = r'<分镜(\d+)>'
        scenes = re.findall(scene_pattern, content)
        scene_numbers = [int(num) for num in scenes]
        
        return {
            'total_scenes': len(scene_numbers),
            'scene_numbers': sorted(scene_numbers),
            'max_scene': max(scene_numbers) if scene_numbers else 0,
            'min_scene': min(scene_numbers) if scene_numbers else 0
        }
    except Exception as e:
        return {'error': str(e)}

def count_scene_files(chapter_dir):
    """
    统计章节目录中的scene文件数量
    """
    scene_files = []
    if os.path.exists(chapter_dir):
        for file in os.listdir(chapter_dir):
            if file.startswith('scene_') and file.endswith('.txt'):
                scene_files.append(file)
    
    return {
        'total_files': len(scene_files),
        'files': sorted(scene_files)
    }

def validate_all_chapters():
    """
    验证所有章节的scene文件生成数量
    """
    data_dir = Path('data')
    results = []
    
    print("验证所有章节的scene文件生成数量...")
    print("=" * 60)
    
    # 遍历所有数据目录
    for book_dir in sorted(data_dir.iterdir()):
        if not book_dir.is_dir() or book_dir.name.startswith('.'):
            continue
            
        print(f"\n📚 书籍: {book_dir.name}")
        print("-" * 40)
        
        # 遍历章节
        for chapter_dir in sorted(book_dir.iterdir()):
            if not chapter_dir.is_dir() or not chapter_dir.name.startswith('chapter_'):
                continue
                
            chapter_name = chapter_dir.name
            narration_file = chapter_dir / 'narration.txt'
            
            # 统计narration.txt中的分镜数量
            narration_stats = {'total_scenes': 0, 'error': 'narration.txt不存在'}
            if narration_file.exists():
                narration_stats = count_scenes_in_narration(narration_file)
            
            # 统计scene文件数量
            scene_file_stats = count_scene_files(chapter_dir)
            
            # 分析结果
            status = "✅"
            issues = []
            
            if 'error' in narration_stats:
                status = "❌"
                issues.append(f"narration.txt问题: {narration_stats['error']}")
            else:
                expected_scenes = narration_stats['total_scenes']
                actual_files = scene_file_stats['total_files']
                
                if expected_scenes != actual_files:
                    status = "⚠️"
                    issues.append(f"数量不匹配: 期望{expected_scenes}个scene，实际{actual_files}个文件")
                
                # 检查scene编号连续性
                if narration_stats.get('scene_numbers'):
                    scene_nums = narration_stats['scene_numbers']
                    expected_range = list(range(1, max(scene_nums) + 1))
                    if scene_nums != expected_range:
                        status = "⚠️"
                        missing = set(expected_range) - set(scene_nums)
                        extra = set(scene_nums) - set(expected_range)
                        if missing:
                            issues.append(f"缺失分镜: {sorted(missing)}")
                        if extra:
                            issues.append(f"额外分镜: {sorted(extra)}")
            
            # 输出结果
            print(f"{status} {chapter_name}")
            if 'error' not in narration_stats:
                print(f"   分镜数量: {narration_stats['total_scenes']}")
                print(f"   scene文件: {scene_file_stats['total_files']}")
                if narration_stats.get('scene_numbers'):
                    print(f"   分镜编号: {narration_stats['scene_numbers']}")
            
            if issues:
                for issue in issues:
                    print(f"   ⚠️  {issue}")
            
            # 记录结果
            results.append({
                'book': book_dir.name,
                'chapter': chapter_name,
                'narration_stats': narration_stats,
                'scene_file_stats': scene_file_stats,
                'status': status,
                'issues': issues
            })
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 总结报告")
    print("=" * 60)
    
    total_chapters = len(results)
    success_count = len([r for r in results if r['status'] == '✅'])
    warning_count = len([r for r in results if r['status'] == '⚠️'])
    error_count = len([r for r in results if r['status'] == '❌'])
    
    print(f"总章节数: {total_chapters}")
    print(f"✅ 正常: {success_count}")
    print(f"⚠️  警告: {warning_count}")
    print(f"❌ 错误: {error_count}")
    
    if warning_count > 0 or error_count > 0:
        print(f"\n需要关注的章节:")
        for result in results:
            if result['status'] != '✅':
                print(f"{result['status']} {result['book']}/{result['chapter']}")
                for issue in result['issues']:
                    print(f"   - {issue}")
    
    return results

if __name__ == "__main__":
    validate_all_chapters()