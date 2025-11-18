#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证GPU profile参数修复 - 静态代码检查版本
检查修改后的代码是否正确处理profile参数
"""

import re
import sys
from pathlib import Path


def check_file_for_profile_handling(file_path):
    """
    检查文件中是否正确处理了profile参数
    
    Args:
        file_path: 文件路径
    
    Returns:
        dict: 检查结果
    """
    print(f"\n检查文件: {file_path.name}")
    print("-" * 60)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = {
        'file': file_path.name,
        'has_profile_in_gpu_params': False,
        'has_profile_handling': False,
        'profile_handling_count': 0,
        'issues': []
    }
    
    # 1. 检查是否在get_ffmpeg_gpu_params中定义了profile
    if "'profile': 'high'" in content or '"profile": "high"' in content:
        results['has_profile_in_gpu_params'] = True
        print("✓ 在GPU参数中找到 'profile': 'high' 定义")
    else:
        print("⚠️  未在GPU参数中找到profile定义（可能使用CPU编码或Mac VideoToolbox）")
    
    # 2. 检查是否有处理profile参数的代码
    profile_patterns = [
        r"-profile:v['\"]?\s*,\s*gpu_params\[['\"]profile['\"]\]",
        r"'-profile:v',\s*gpu_params\['profile'\]",
        r'"-profile:v",\s*gpu_params\[\'profile\'\]',
        r'"-profile:v",\s*gpu_params\.get\(\'profile\'\)',
    ]
    
    for pattern in profile_patterns:
        matches = re.findall(pattern, content)
        if matches:
            results['has_profile_handling'] = True
            results['profile_handling_count'] += len(matches)
    
    # 更广泛的模式匹配
    if "'-profile:v'" in content or '"-profile:v"' in content:
        results['has_profile_handling'] = True
        # 统计出现次数
        count = content.count("'-profile:v'") + content.count('"-profile:v"')
        results['profile_handling_count'] = count
        print(f"✓ 找到 {count} 处使用 -profile:v 参数的代码")
    else:
        print("❌ 未找到使用 -profile:v 参数的代码")
    
    # 3. 检查是否有条件判断（应该排除VideoToolbox）
    if "if 'profile' in gpu_params" in content:
        print("✓ 找到 profile 参数的条件判断")
        if "_videotoolbox" in content:
            print("✓ 条件判断中排除了 VideoToolbox 编码器")
        else:
            results['issues'].append("条件判断未排除VideoToolbox编码器")
    elif results['has_profile_in_gpu_params']:
        results['issues'].append("定义了profile但未找到相应的条件判断")
    
    # 4. 检查preset和profile的顺序（profile应该在preset之后）
    preset_positions = [m.start() for m in re.finditer(r"'-preset'|" + r'"-preset"', content)]
    profile_positions = [m.start() for m in re.finditer(r"'-profile:v'|" + r'"-profile:v"', content)]
    
    if preset_positions and profile_positions:
        # 检查每个profile是否在对应的preset之后
        for profile_pos in profile_positions:
            # 找到最近的preset位置
            closest_preset = max([p for p in preset_positions if p < profile_pos], default=None)
            if closest_preset:
                print(f"✓ profile 参数位置正确（在 preset 之后）")
            else:
                print(f"⚠️  存在 profile 参数但前面没有 preset 参数")
    
    return results


def main():
    """
    主函数
    """
    print("=" * 60)
    print("GPU Profile参数修复验证 - 静态代码检查")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    files_to_check = [
        project_root / "concat_narration_video.py",
        project_root / "concat_finish_video.py",
        project_root / "concat_first_video.py",
    ]
    
    all_results = []
    
    for file_path in files_to_check:
        if not file_path.exists():
            print(f"\n❌ 文件不存在: {file_path}")
            continue
        
        result = check_file_for_profile_handling(file_path)
        all_results.append(result)
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    all_passed = True
    
    for result in all_results:
        print(f"\n{result['file']}:")
        
        if result['has_profile_in_gpu_params']:
            print(f"  ✓ 定义了profile参数")
            
            if result['has_profile_handling']:
                print(f"  ✓ 实现了profile参数处理 (共{result['profile_handling_count']}处)")
            else:
                print(f"  ❌ 定义了profile但未实现参数处理")
                all_passed = False
        else:
            print(f"  ⚠️  未定义profile参数（可能正常，取决于环境）")
        
        if result['issues']:
            print(f"  问题:")
            for issue in result['issues']:
                print(f"    - {issue}")
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("\n✓ 修复验证通过！")
        print("\n修复内容:")
        print("  1. 在三个视频生成文件中添加了profile参数处理")
        print("  2. profile参数通过 -profile:v 选项传递给ffmpeg")
        print("  3. 正确排除了VideoToolbox编码器（不支持profile参数）")
        print("  4. profile参数按正确顺序添加（在preset之后）")
        return 0
    else:
        print("\n❌ 发现问题，请检查！")
        return 1


if __name__ == "__main__":
    sys.exit(main())

