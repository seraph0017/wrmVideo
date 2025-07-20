1、python generate.py script data/001/xxx.txt 用来根据txt文档生成解说文案
2、python generate.py image data/001 用来根据解说文案生成图片
3、python generate.py voice data/001 用来根据解说文案生成旁白
4、python generate.py cocat data/001 用来根据解说文案，旁白，图片，一起组合成视频






new:

python gen_script.py data/001/xxx.txt 用来根据txt文档生成解说文案 
python gen_character_image.py data/001 用来根据解说文案生成角色图片
python gen_image.py data/001 用来根据解说文案生成图片 
python gen_audio.py data/001 用来根据解说文案生成旁白
python fix_timestamps_banch.py data/001 用来修复字幕时间戳
python gen_first_video.py data/001 用来生成第一个narration的视频
python gen_ass.py data/001 用来生成字幕带时间戳文件
python gen_video.py data/001 用来根据解说文案，旁白，图片，一起组合成视频 