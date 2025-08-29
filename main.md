old:

python gen_script.py data/001/xxx.txt 用来根据txt文档生成解说文案 
python gen_image_async.py data/001 用来根据解说文案生成图片 
python check_async_tasks.py --monitor 来收图
python gen_audio.py data/001 用来根据解说文案生成旁白
python gen_first_video_async.py data/001 用来异步生成第一个narration的视频
python check_async_tasks.py --monitor 来收图
python gen_ass.py data/001 用来生成字幕带时间戳文件
python gen_video.py data/001 用来根据解说文案，旁白，图片，一起组合成视频

new:



python check_async_tasks.py 开启异步队列



python gen_script_v2.py data/001 用来根据文本生成解说文案，带检查
python validate_narration.py data/001 --auto-rewrite 用来验证解说文案字数
python gen_character_image.py data/001 用来根据文本生成角色图片
python llm_image.py data/001 --auto-regenerate 用来检测图片是否符合要求并替换
python gen_audio.py data/001 用来根据解说文案生成旁白
python gen_ass.py data/001 用来生成字幕带时间戳文件
python gen_image_async.py data/001 用来根据解说文案和角色生成图片
python check_async_tasks.py --monitor
python llm_narration_image.py data/001 --auto-regenerate 用来检测图片是否符合要求并替换
python gen_first_video_async.py data/001 用来异步生成第一个narration的视频
python check_async_tasks.py --monitor
python rename_images.py data/001 重命名图片
python gen_video.py data/001 生成整个视频
python upload_tos.py data/001 上传视频到tos