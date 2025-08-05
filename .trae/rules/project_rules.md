1. python gen_script.py data/001/xxx.txt 用来根据txt文档生成解说文案  用gevent实现异步处理
2. python gen_image.py data/001 用来根据解说文案生成图片 主要是图生图 用Character_Images目录里面的图片
3. python gen_audio.py data/001 用来根据解说文案生成旁白 用gevent实现异步
4. python gen_first_video.py data/001 用来生成第一个narration的视频
5. python gen_ass.py data/001 用来生成字幕带时间戳文件
6. python gen_video.py data/001 用来根据解说文案，旁白，图片，一起组合成视频 


7. data目录是所有的文件目录
8. Character_Images目录是所有的角色图片目录
9. sound是补充的音频文件目录