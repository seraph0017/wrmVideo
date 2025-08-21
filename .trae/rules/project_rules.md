python check_async_tasks.py 开启异步队列



python gen_script_v2.py data/001 用来根据文本生成解说文案，带检查
python gen_character_image.py data/001 用来根据文本生成角色图片
python llm_image.py data/001 用来检测图片是否符合要求并替换
python gen_audio.py data/001 用来根据解说文案生成旁白
python gen_ass.py data/001 用来生成字幕带时间戳文件
python gen_image_async.py data/001 用来根据解说文案和角色生成图片
python llm_narration_image.py data/001 用来检测图片是否符合要求并替换
python gen_first_video_async.py data/001 用来异步生成第一个narration的视频
python gen_video.py data/001 生成整个视频
python upload_tos.py data/001 上传视频到tos


7. data目录是所有的文件目录
8. Character_Images目录是所有的角色图片目录
9. sound是补充的音频文件目录