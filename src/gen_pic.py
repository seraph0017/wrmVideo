import os
import base64
import requests
from datetime import datetime
from volcenginesdkarkruntime import Ark
from config import ARK_CONFIG

# 艺术风格模板
ART_STYLES = {
    'manga': (
        "漫画风格，动漫插画，精美细腻的画风，鲜艳的色彩，清晰的线条，"
        "日式动漫风格，高质量插画，细节丰富，光影效果好，"
    ),
    'realistic': (
        "写实风格，真实感强，细节丰富，高清画质，专业摄影，"
        "自然光线，真实色彩，"
    ),
    'watercolor': (
        "水彩画风格，柔和的色彩，艺术感强，手绘质感，"
        "淡雅的色调，水彩晕染效果，"
    ),
    'oil_painting': (
        "油画风格，厚重的笔触，丰富的色彩层次，古典艺术感，"
        "油画质感，艺术大师风格，"
    )
}

# 初始化Ark客户端
client = Ark(
    base_url=ARK_CONFIG['base_url'],
    api_key=ARK_CONFIG['api_key'],
)

def generate_image_with_style(description, style='manga', output_path=None):
    """
    根据描述和风格生成图片
    
    Args:
        description: 图片描述文本
        style: 艺术风格 ('manga', 'realistic', 'watercolor', 'oil_painting')
        output_path: 输出文件路径，如果为None则自动生成
    
    Returns:
        str: 生成的图片文件路径，失败返回None
    """
    try:
        # 获取风格模板
        style_prompt = ART_STYLES.get(style, ART_STYLES['manga'])
        
        # 构建完整的prompt
        full_prompt = style_prompt + "以下面一段描述为描述，生成一张故事图片\n\n" + description
        
        print(f"正在生成{style}风格图片...")
        
        imagesResponse = client.images.generate(
            model="doubao-seedream-3-0-t2i-250415",
            prompt=full_prompt,
            watermark=False,
            size="720x1280",
            response_format="b64_json"
        )
        
        # 处理base64格式的图片数据并保存
        if hasattr(imagesResponse.data[0], 'b64_json') and imagesResponse.data[0].b64_json:
            # 确保data目录存在
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # 生成文件路径
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"generated_image_{style}_{timestamp}.jpg"
                output_path = os.path.join(data_dir, image_filename)
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 解码base64数据并保存
            image_data = base64.b64decode(imagesResponse.data[0].b64_json)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"图片已保存到: {output_path}")
            return output_path
        else:
            print("未获取到base64格式的图片数据")
            return None
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return None

# 测试用的描述文本
test_description = """
晨露还趴在蕨类植物的绒毛上打盹，森林的第一声'沙沙'就挠醒了我的指尖。那些爬满青苔的树干突然睁开'眼睛'，绿色符文像被惊醒的萤火虫，在树皮上跳着古老的圆舞曲。（指尖触碰树干的轻响，符文闪烁的音效）  
传说中会吞噬旅人的低语森林，此刻正用潮湿的呼吸，轻轻舔舐着闯入者的衣角。我忽然明白，真正的危险从不是未知，而是你以为自己早已看透了未知。
"""

if __name__ == '__main__':
    # 可以在这里修改风格和描述
    style = 'manga'  # 可选: 'manga', 'realistic', 'watercolor', 'oil_painting'
    
    print(f"使用{style}风格生成图片...")
    print("可用风格: manga(漫画), realistic(写实), watercolor(水彩), oil_painting(油画)")
    
    # 生成图片
    result_path = generate_image_with_style(test_description, style)
    
    if result_path:
        print(f"图片生成成功！文件保存在: {result_path}")
    else:
        print("图片生成失败！")
    
    # 演示不同风格（可选）
    demo_styles = False  # 设置为True来生成所有风格的示例
    if demo_styles:
        print("\n正在生成所有风格的示例图片...")
        for style_name in ART_STYLES.keys():
            print(f"\n生成{style_name}风格...")
            generate_image_with_style(test_description, style_name)