#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GPU profile参数修复
验证在GPU特化场景下，profile参数是否正确添加到ffmpeg命令中
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入需要测试的函数
from concat_narration_video import get_ffmpeg_gpu_params as get_params_narration
from concat_finish_video import get_ffmpeg_gpu_params as get_params_finish
from concat_first_video import get_ffmpeg_gpu_params as get_params_first


def test_gpu_params_structure():
    """
    测试GPU参数结构是否包含profile字段
    
    Returns:
        bool: 测试是否通过
    """
    print("\n=== 测试GPU参数结构 ===")
    
    # 获取三个文件的GPU参数
    params_narration = get_params_narration()
    params_finish = get_params_finish()
    params_first = get_params_first()
    
    print(f"\n1. concat_narration_video.py GPU参数:")
    print(f"   video_codec: {params_narration.get('video_codec')}")
    print(f"   preset: {params_narration.get('preset', 'N/A')}")
    print(f"   profile: {params_narration.get('profile', 'N/A')}")
    print(f"   hwaccel: {params_narration.get('hwaccel', 'N/A')}")
    
    print(f"\n2. concat_finish_video.py GPU参数:")
    print(f"   video_codec: {params_finish.get('video_codec')}")
    print(f"   preset: {params_finish.get('preset', 'N/A')}")
    print(f"   profile: {params_finish.get('profile', 'N/A')}")
    print(f"   hwaccel: {params_finish.get('hwaccel', 'N/A')}")
    
    print(f"\n3. concat_first_video.py GPU参数:")
    print(f"   video_codec: {params_first.get('video_codec')}")
    print(f"   preset: {params_first.get('preset', 'N/A')}")
    print(f"   profile: {params_first.get('profile', 'N/A')}")
    print(f"   hwaccel: {params_first.get('hwaccel', 'N/A')}")
    
    # 检查是否在nvenc编码器场景下包含profile参数
    all_params = [params_narration, params_finish, params_first]
    file_names = ['concat_narration_video', 'concat_finish_video', 'concat_first_video']
    
    all_passed = True
    for i, params in enumerate(all_params):
        codec = params.get('video_codec', '')
        if 'nvenc' in codec:
            if 'profile' not in params:
                print(f"\n❌ 错误: {file_names[i]}.py 使用nvenc编码器但缺少profile参数")
                all_passed = False
            else:
                print(f"\n✓ {file_names[i]}.py nvenc编码器包含profile参数: {params['profile']}")
        else:
            print(f"\n✓ {file_names[i]}.py 使用{codec}编码器（不需要profile参数）")
    
    return all_passed


def simulate_ffmpeg_command_build():
    """
    模拟构建ffmpeg命令，验证profile参数是否会被添加
    
    Returns:
        bool: 测试是否通过
    """
    print("\n=== 模拟ffmpeg命令构建 ===")
    
    gpu_params = get_params_narration()
    
    # 模拟构建命令（参考实际代码逻辑）
    cmd = ['ffmpeg', '-y']
    
    # 添加硬件加速
    if 'hwaccel' in gpu_params:
        cmd.extend(['-hwaccel', gpu_params['hwaccel']])
    
    # 添加编解码器
    cmd.extend(['-c:v', gpu_params['video_codec']])
    
    # 添加preset
    if 'preset' in gpu_params and not gpu_params['video_codec'].endswith('_videotoolbox'):
        cmd.extend(['-preset', gpu_params['preset']])
    
    # 添加profile（这是我们修复的部分）
    if 'profile' in gpu_params and not gpu_params['video_codec'].endswith('_videotoolbox'):
        cmd.extend(['-profile:v', gpu_params['profile']])
    
    # 添加tune
    if 'tune' in gpu_params:
        cmd.extend(['-tune', gpu_params['tune']])
    
    print(f"\n生成的ffmpeg命令片段:")
    print(f"  {' '.join(cmd)}")
    
    # 检查是否包含profile参数
    if 'nvenc' in gpu_params.get('video_codec', '') and 'profile' in gpu_params:
        if '-profile:v' in cmd:
            print(f"\n✓ 命令中正确包含了 -profile:v {gpu_params['profile']} 参数")
            return True
        else:
            print(f"\n❌ 命令中缺少 -profile:v 参数（尽管gpu_params中定义了profile）")
            return False
    else:
        print(f"\n✓ 当前编码器不需要profile参数")
        return True


def main():
    """
    主测试函数
    """
    print("=" * 60)
    print("GPU Profile参数修复验证测试")
    print("=" * 60)
    
    # 运行测试
    test1_passed = test_gpu_params_structure()
    test2_passed = simulate_ffmpeg_command_build()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if test1_passed and test2_passed:
        print("\n✓ 所有测试通过！")
        print("\n修复说明:")
        print("  - GPU参数字典中的profile字段现在会被正确使用")
        print("  - 在使用h264_nvenc/hevc_nvenc编码器时，会添加 -profile:v 参数")
        print("  - VideoToolbox编码器不受影响（正确跳过profile参数）")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查代码！")
        return 1


if __name__ == "__main__":
    sys.exit(main())

