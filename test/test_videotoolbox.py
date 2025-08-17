#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试macOS VideoToolbox硬件编码器检测功能
"""

import subprocess
import platform

def check_macos_videotoolbox():
    """检测macOS系统是否支持VideoToolbox硬件编码器"""
    try:
        if platform.system() != 'Darwin':
            print("❌ 当前系统不是macOS，VideoToolbox不可用")
            return False, None
        
        print("✓ 检测到macOS系统")
        
        # 测试h264_videotoolbox编码器
        print("正在测试 h264_videotoolbox 编码器...")
        test_cmd_h264 = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-c:v', 'h264_videotoolbox', '-f', 'null', '-'
        ]
        result_h264 = subprocess.run(test_cmd_h264, capture_output=True, text=False, timeout=15)
        h264_available = result_h264.returncode == 0
        
        # 测试hevc_videotoolbox编码器
        print("正在测试 hevc_videotoolbox 编码器...")
        test_cmd_hevc = [
            'ffmpeg', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1',
            '-c:v', 'hevc_videotoolbox', '-f', 'null', '-'
        ]
        result_hevc = subprocess.run(test_cmd_hevc, capture_output=True, text=False, timeout=15)
        hevc_available = result_hevc.returncode == 0
        
        print("\n=== VideoToolbox 检测结果 ===")
        if h264_available or hevc_available:
            print("✓ 检测到macOS VideoToolbox硬件编码器")
            if h264_available:
                print("  ✓ h264_videotoolbox 可用")
            else:
                print("  ❌ h264_videotoolbox 不可用")
                
            if hevc_available:
                print("  ✓ hevc_videotoolbox 可用")
            else:
                print("  ❌ hevc_videotoolbox 不可用")
                
            return True, {'h264': h264_available, 'hevc': hevc_available}
        else:
            print("❌ VideoToolbox编码器不可用")
            if not h264_available:
                try:
                    stderr_h264 = result_h264.stderr.decode('utf-8', errors='ignore')
                    print(f"  h264_videotoolbox 错误: {stderr_h264[:200]}...")
                except:
                    pass
            if not hevc_available:
                try:
                    stderr_hevc = result_hevc.stderr.decode('utf-8', errors='ignore')
                    print(f"  hevc_videotoolbox 错误: {stderr_hevc[:200]}...")
                except:
                    pass
            return False, None
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"❌ VideoToolbox检测失败: {e}")
        return False, None

def test_ffmpeg_availability():
    """测试FFmpeg是否可用"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ FFmpeg 可用")
            # 提取版本信息
            version_line = result.stdout.split('\n')[0]
            print(f"  版本: {version_line}")
            return True
        else:
            print("❌ FFmpeg 不可用")
            return False
    except Exception as e:
        print(f"❌ FFmpeg 检测失败: {e}")
        return False

def main():
    print("=== macOS VideoToolbox 硬件编码器检测测试 ===")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print()
    
    # 首先检测FFmpeg
    if not test_ffmpeg_availability():
        print("\n请先安装FFmpeg: brew install ffmpeg")
        return
    
    print()
    
    # 检测VideoToolbox
    videotoolbox_available, videotoolbox_info = check_macos_videotoolbox()
    
    print("\n=== 建议的编码器配置 ===")
    if videotoolbox_available:
        if videotoolbox_info['h264']:
            print("推荐使用: h264_videotoolbox")
            print("FFmpeg参数示例:")
            print("  -c:v h264_videotoolbox -allow_sw 1 -realtime 1")
        elif videotoolbox_info['hevc']:
            print("推荐使用: hevc_videotoolbox")
            print("FFmpeg参数示例:")
            print("  -c:v hevc_videotoolbox -allow_sw 1 -realtime 1")
    else:
        print("推荐使用: libx264 (软件编码)")
        print("FFmpeg参数示例:")
        print("  -c:v libx264 -preset fast")

if __name__ == '__main__':
    main()