import os
import ffmpeg
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
        
        # 使用ffmpeg-python合成视频
        print(f"正在合成视频: {video_filename}")
        
        # 创建输入流
        image_input = ffmpeg.input(image_path, loop=1)
        audio_input = ffmpeg.input(audio_path)
        
        # 合成视频
        output = ffmpeg.output(
            image_input, audio_input,
            video_path,
            vcodec='libx264',
            acodec='aac',
            pix_fmt='yuv420p',
            shortest=None
        )
        
        # 运行ffmpeg命令
        ffmpeg.run(output, overwrite_output=True, quiet=True)
        
        # 检查输出文件是否存在
        if os.path.exists(video_path):
            print(f"视频合成成功: {video_path}")
            return video_path
        else:
            print("视频合成失败: 输出文件未生成")
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