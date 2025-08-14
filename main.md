new:

python gen_script.py data/001/xxx.txt 用来根据txt文档生成解说文案 
python gen_image_async.py data/001 用来根据解说文案生成图片 
python check_async_tasks.py --monitor 来收图
python gen_audio.py data/001 用来根据解说文案生成旁白
python gen_first_video_async.py data/001 用来异步生成第一个narration的视频
python check_async_tasks.py --monitor 来收图
python gen_ass.py data/001 用来生成字幕带时间戳文件
python gen_video.py data/001 用来根据解说文案，旁白，图片，一起组合成视频