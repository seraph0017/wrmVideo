import os
import subprocess
from datetime import datetime

def concat_video(image_path, audio_path, output_dir):
    """
    将图片和音频合成为视频
    
    Args:
        image_path: 图片文件路径
        audio_path: 音频文件路径
        output_dir: 输出目录
    
    Returns:
        str: 生成的视频文件路径
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成带时间戳的视频文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"video_{timestamp}.mp4"
        video_path = os.path.join(output_dir, video_filename)
        
        # 使用ffmpeg合成视频
        # -loop 1: 循环图片
        # -i: 输入文件
        # -c:v libx264: 视频编码器
        # -t: 视频时长（根据音频时长）
        # -pix_fmt yuv420p: 像素格式
        # -shortest: 以最短的输入为准
        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-y',  # 覆盖输出文件
            video_path
        ]
        
        print(f"正在合成视频: {video_filename}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"视频合成成功: {video_path}")
            return video_path
        else:
            print(f"视频合成失败: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"视频合成过程中发生错误: {e}")
        return None

if __name__ == '__main__':
    # 测试用例
    image_path = "test_image.jpg"
    audio_path = "test_audio.mp3"
    output_dir = "../data"
    
    video_path = concat_video(image_path, audio_path, output_dir)
    if video_path:
        print(f"测试完成，视频保存在: {video_path}")
    else:
        print("测试失败")