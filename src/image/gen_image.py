# coding:utf-8
from __future__ import print_function
import base64
import os

from volcengine.visual.VisualService import VisualService
from config.config import IMAGE_TWO_CONFIG


def generate_image_with_volcengine(prompt, output_path):
    """
    使用火山引擎生成图片并保存
    
    Args:
        prompt: 图片描述文本
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功生成并保存图片
    """
    try:
        visual_service = VisualService()
        
        # 设置访问密钥
        visual_service.set_ak(IMAGE_TWO_CONFIG['access_key'])
        visual_service.set_sk(IMAGE_TWO_CONFIG['secret_key'])
        
        # 请求参数 - 使用配置文件中的值
        form = {
            "req_key": IMAGE_TWO_CONFIG['req_key'],
            "prompt": prompt,
            "llm_seed": -1,
            "seed": -1,
            "scale": IMAGE_TWO_CONFIG['scale'],
            "ddim_steps": IMAGE_TWO_CONFIG['ddim_steps'],
            "width": IMAGE_TWO_CONFIG['default_width'],
            "height": IMAGE_TWO_CONFIG['default_height'],
            "use_pre_llm": IMAGE_TWO_CONFIG['use_pre_llm'],
            "use_sr": IMAGE_TWO_CONFIG['use_sr'],
            "return_url": IMAGE_TWO_CONFIG['return_url'],  # 返回base64格式
            "logo_info": {
                "add_logo": False,
                "position": 0,
                "language": 0,
                "opacity": 0.3,
                "logo_text_content": "这里是明水印内容"
            }
        }
        
        print(f"正在生成图片: {os.path.basename(output_path)}")
        resp = visual_service.cv_process(form)
        
        # 检查响应
        if 'data' in resp and 'binary_data_base64' in resp['data']:
            # 获取base64图片数据
            base64_data = resp['data']['binary_data_base64'][0]  # 取第一张图片
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 解码并保存图片
            image_data = base64.b64decode(base64_data)
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            print(f"图片已保存: {output_path}")
            return True
        else:
            print(f"图片生成失败: {resp}")
            return False
            
    except Exception as e:
        print(f"生成图片时发生错误: {e}")
        return False


if __name__ == '__main__':
    # 测试用例
    test_prompt = "千军万马"
    test_output = "test_image.jpg"
    
    success = generate_image_with_volcengine(test_prompt, test_output)
    if success:
        print("测试成功")
    else:
        print("测试失败")