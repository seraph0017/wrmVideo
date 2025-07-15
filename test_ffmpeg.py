import ffmpeg
import os
import json

def get_video_info(video_path):
    """获取视频的分辨率和帧率"""
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is None:
        raise ValueError("找不到视频流")
    
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    
    # 解析帧率（可能是分数形式，如 "30000/1000"）
    r_frame_rate = video_stream['r_frame_rate']
    fps_num, fps_den = map(int, r_frame_rate.split('/'))
    fps = fps_num / fps_den
    
    return width, height, fps

def image_to_video(image_path, output_path, duration=3, width=1920, height=1080, fps=30):
    """将图片转换为视频片段"""
    (
        ffmpeg
        .input(image_path, loop=1, t=duration)
        .filter('scale', width, height)
        .output(output_path, r=fps, vcodec='libx264', pix_fmt='yuv420p')
        .overwrite_output()
        .run()
    )
    print(f"图片转视频成功：{output_path}")

def concat_videos(video_list, output_path):
    """拼接多个视频片段，处理不同格式和流情况"""
    # 检查每个输入文件是否有音频流
    has_audio = []
    for video in video_list:
        probe = ffmpeg.probe(video)
        audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
        has_audio.append(len(audio_streams) > 0)
    
    # 创建输入流
    inputs = [ffmpeg.input(v) for v in video_list]
    
    # 根据是否所有输入都有音频，调整concat参数
    if all(has_audio):
        # 所有输入都有音频，拼接视频和音频
        stream = ffmpeg.concat(*inputs, v=1, a=1).output(output_path)
    elif not any(has_audio):
        # 所有输入都没有音频，只拼接视频
        stream = ffmpeg.concat(*inputs, v=1, a=0).output(output_path)
    else:
        # 部分输入有音频，需要特殊处理（这里选择忽略音频）
        print("警告：部分输入有音频，部分没有。拼接结果将不含音频。")
        video_streams = [i.video for i in inputs]
        stream = ffmpeg.concat(*video_streams, v=1, a=0).output(output_path)
    
    # 执行拼接
    stream.overwrite_output().run()
    print(f"视频拼接成功：{output_path}")

def add_subtitle(video_path, subtitle_path, output_path):
    """为视频添加硬字幕"""
    (
        ffmpeg
        .input(video_path)
        .filter('subtitles', subtitle_path)
        .output(output_path)
        .overwrite_output()
        .run()
    )
    print(f"添加字幕成功：{output_path}")

def add_audio(video_path, audio_path, output_path, replace=True):
    """为视频添加音频（替换或混合）"""
    video = ffmpeg.input(video_path)
    audio = ffmpeg.input(audio_path)
    
    if replace:
        # 替换原音频
        (
            ffmpeg
            .output(video.video, audio.audio, output_path, c='copy')
            .overwrite_output()
            .run()
        )
    else:
        # 混合原音频和新音频
        (
            ffmpeg
            .filter([video.audio, audio.audio], 'amix', inputs=2, duration='shortest')
            .output(video.video, 'a', output_path)
            .overwrite_output()
            .run()
        )
    print(f"添加音频成功：{output_path}")





def main():
    # 输入文件路径
    image_path = "/Users/nathan/Projects/wrmVideo/data/002/chapter_002/chapter_002_image_02.jpeg"
    original_video = "/Users/nathan/Projects/wrmVideo/data/002/chapter_002/chapter_002_combined_video.mp4"
    subtitle_path = "/Users/nathan/Projects/wrmVideo/data/002/chapter_002/chapter_002_narration_01.ass"
    audio_path = "/Users/nathan/Projects/wrmVideo/data/002/chapter_002/chapter_002_narration_01.mp3"

    # 输出文件路径
    image_video = "test_ffmpeg/image.mp4"
    concatenated_video = "test_ffmpeg/concatenated.mp4"
    video_with_sub = "test_ffmpeg/video_with_sub.mp4"
    final_output = "test_ffmpeg/final_output.mp4"

    try:
        # 1. 获取原视频参数
        width, height, fps = get_video_info(original_video)
        
        # 2. 图片转视频
        image_to_video(image_path, image_video, duration=10, width=width, height=height, fps=fps)
        
        # 3. 拼接视频
        concat_videos([original_video, image_video], concatenated_video)
        
        # 4. 添加字幕
        add_subtitle(concatenated_video, subtitle_path, video_with_sub)
        
        # 5. 添加音频
        add_audio(video_with_sub, audio_path, final_output, replace=True)

        # print("所有操作完成！最终文件：", final_output)

    except Exception as e:
        print("流程失败：", e)
    finally:
        pass
        # 清理中间文件
        # for f in [image_video, concatenated_video, video_with_sub]:
        #     if os.path.exists(f):
        #         os.remove(f)

if __name__ == "__main__":
    main()