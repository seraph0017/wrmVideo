import os
from volcenginesdkarkruntime import Ark
from config import ARK_CONFIG

# 初始化Ark客户端
client = Ark(
    base_url=ARK_CONFIG['base_url'],
    api_key=ARK_CONFIG['api_key'],
)

prompt = """
以下面一段描述为描述，生成一张故事图片

晨露还趴在蕨类植物的绒毛上打盹，森林的第一声'沙沙'就挠醒了我的指尖。那些爬满青苔的树干突然睁开'眼睛'，绿色符文像被惊醒的萤火虫，在树皮上跳着古老的圆舞曲。（指尖触碰树干的轻响，符文闪烁的音效）  
传说中会吞噬旅人的低语森林，此刻正用潮湿的呼吸，轻轻舔舐着闯入者的衣角。我忽然明白，真正的危险从不是未知，而是你以为自己早已看透了未知。
"""

imagesResponse = client.images.generate(
    model="doubao-seedream-3-0-t2i-250415",
    prompt=prompt,
    watermark=False,
    size="720x1280"
)

print(imagesResponse.data[0].url)