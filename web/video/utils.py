import os
import docx
import PyPDF2
import tos
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings


def handle_uploaded_file(uploaded_file):
    """
    处理上传的文件并提取文本内容
    
    Args:
        uploaded_file: Django UploadedFile 对象
        
    Returns:
        str: 提取的文本内容
    """
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    try:
        if file_extension == '.txt':
            return extract_text_from_txt(uploaded_file)
        elif file_extension in ['.doc', '.docx']:
            return extract_text_from_docx(uploaded_file)
        elif file_extension == '.pdf':
            return extract_text_from_pdf(uploaded_file)
        else:
            raise ValueError(f"不支持的文件格式: {file_extension}")
    except Exception as e:
        raise ValueError(f"文件解析失败: {str(e)}")


def extract_text_from_txt(uploaded_file):
    """
    从TXT文件中提取文本
    
    Args:
        uploaded_file: Django UploadedFile 对象
        
    Returns:
        str: 文本内容
    """
    try:
        # 尝试不同的编码格式
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
        
        for encoding in encodings:
            try:
                uploaded_file.seek(0)  # 重置文件指针
                content = uploaded_file.read().decode(encoding)
                return content
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，使用utf-8并忽略错误
        uploaded_file.seek(0)
        content = uploaded_file.read().decode('utf-8', errors='ignore')
        return content
        
    except Exception as e:
        raise ValueError(f"TXT文件读取失败: {str(e)}")


def extract_text_from_docx(uploaded_file):
    """
    从DOCX文件中提取文本
    
    Args:
        uploaded_file: Django UploadedFile 对象
        
    Returns:
        str: 文本内容
    """
    try:
        # 保存临时文件
        temp_file_path = default_storage.save(
            f'temp/{uploaded_file.name}',
            ContentFile(uploaded_file.read())
        )
        
        # 获取完整路径
        full_path = os.path.join(settings.MEDIA_ROOT, temp_file_path)
        
        # 读取docx文件
        doc = docx.Document(full_path)
        text_content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        # 删除临时文件
        default_storage.delete(temp_file_path)
        
        return '\n'.join(text_content)
        
    except Exception as e:
        # 确保删除临时文件
        try:
            default_storage.delete(temp_file_path)
        except:
            pass
        raise ValueError(f"DOCX文件读取失败: {str(e)}")


def extract_text_from_pdf(uploaded_file):
    """
    从PDF文件中提取文本
    
    Args:
        uploaded_file: Django UploadedFile 对象
        
    Returns:
        str: 文本内容
    """
    try:
        uploaded_file.seek(0)  # 重置文件指针
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text_content = []
        
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text.strip():
                text_content.append(text)
        
        return '\n'.join(text_content)
        
    except Exception as e:
        raise ValueError(f"PDF文件读取失败: {str(e)}")


def save_uploaded_file(uploaded_file, novel_name):
    """
    保存上传的文件到指定目录
    
    Args:
        uploaded_file: Django UploadedFile 对象
        novel_name: 小说名称，用于创建目录
        
    Returns:
        str: 保存的文件路径
    """
    try:
        # 创建文件名
        file_extension = os.path.splitext(uploaded_file.name)[1]
        safe_novel_name = "".join(c for c in novel_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_novel_name}{file_extension}"
        
        # 保存文件
        file_path = f'novels/{filename}'
        saved_path = default_storage.save(file_path, uploaded_file)
        
        return saved_path
        
    except Exception as e:
        raise ValueError(f"文件保存失败: {str(e)}")


def get_file_info(file_path):
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: 文件信息字典
    """
    try:
        if not default_storage.exists(file_path):
            return None
            
        file_size = default_storage.size(file_path)
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1]
        
        return {
            'name': file_name,
            'size': file_size,
            'extension': file_extension,
            'size_mb': round(file_size / (1024 * 1024), 2)
        }
        
    except Exception as e:
        return None


def upload_novel_to_tos(novel_id, file_path, original_filename):
    """
    上传小说文件到TOS存储服务
    
    Args:
        novel_id (int): 小说ID，用作TOS路径前缀
        file_path (str): 本地文件路径
        original_filename (str): 原始文件名
        
    Returns:
        dict: 包含上传结果的字典
    """
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"[TOS上传] 开始上传小说文件，小说ID: {novel_id}")
        logger.info(f"[TOS上传] 本地文件路径: {file_path}")
        logger.info(f"[TOS上传] 原始文件名: {original_filename}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"本地文件不存在: {file_path}"
            logger.error(f"[TOS上传] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': error_msg
            }
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        logger.info(f"[TOS上传] 文件大小: {file_size} bytes ({file_size/1024/1024:.2f} MB)")
        
        # 从settings中获取TOS配置
        from django.conf import settings
        tos_config = settings.TOS_CONFIG
        bucket_name = tos_config['bucket']
        
        logger.info(f"[TOS上传] TOS配置 - Endpoint: {tos_config['endpoint']}")
        logger.info(f"[TOS上传] TOS配置 - Region: {tos_config['region']}")
        logger.info(f"[TOS上传] TOS配置 - Bucket: {bucket_name}")
        logger.info(f"[TOS上传] TOS配置 - Access Key: {tos_config['access_key'][:10]}...")
        
        # 创建TOS客户端
        logger.info(f"[TOS上传] 正在创建TOS客户端...")
        client = tos.TosClientV2(
            tos_config['access_key'],
            tos_config['secret_key'],
            tos_config['endpoint'],
            tos_config['region']
        )
        logger.info(f"[TOS上传] TOS客户端创建成功")
        
        # 构建TOS对象键名：使用小说ID作为前缀
        object_key = f"{novel_id}/{original_filename}"
        logger.info(f"[TOS上传] 目标对象键: {object_key}")
        
        logger.info(f"[TOS上传] 开始上传文件: {file_path} -> tos://{bucket_name}/{object_key}")
        
        # 上传文件
        with open(file_path, 'rb') as f:
            logger.info(f"[TOS上传] 文件已打开，开始上传...")
            result = client.put_object(bucket_name, object_key, content=f)
            logger.info(f"[TOS上传] 上传响应: {result}")
        
        logger.info(f"[TOS上传] ✓ 小说文件上传成功: {object_key}")
        
        return {
            'success': True,
            'bucket': bucket_name,
            'object_key': object_key,
            'url': f"tos://{bucket_name}/{object_key}",
            'message': '文件上传成功'
        }
        
    except ImportError as e:
        error_msg = f"TOS SDK导入失败: {str(e)}，请确保已安装tos包"
        logger.error(f"[TOS上传] {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'message': error_msg
        }
    except Exception as e:
        error_msg = f"上传失败: {str(e)}"
        logger.error(f"[TOS上传] ✗ {error_msg}")
        logger.error(f"[TOS上传] 错误类型: {type(e).__name__}")
        logger.error(f"[TOS上传] 错误详情: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': error_msg
        }


def parse_narration_file(narration_content):
    """
    解析解说文案XML内容，提取章节信息、出镜人物和分镜内容
    
    Args:
        narration_content (str): 解说文案的XML内容
        
    Returns:
        dict: 包含章节信息、人物信息和分镜信息的字典
    """
    import re
    
    result = {
        'chapter_info': {},
        'characters': [],
        'narrations': []
    }
    
    try:
        # 提取章节基本信息
        chapter_match = re.search(r'<第(\d+)章节>', narration_content)
        if chapter_match:
            result['chapter_info']['chapter_number'] = int(chapter_match.group(1))
        
        # 提取章节风格
        style_match = re.search(r'<章节风格>(.*?)</章节风格>', narration_content)
        if style_match:
            result['chapter_info']['format'] = style_match.group(1)
        
        # 提取绘画风格
        paint_style_match = re.search(r'<绘画风格>(.*?)</绘画风格>', narration_content)
        if paint_style_match:
            result['chapter_info']['paint_style'] = paint_style_match.group(1)
        
        # 提取出镜人物信息
        characters_section = re.search(r'<出镜人物>(.*?)</出镜人物>', narration_content, re.DOTALL)
        if characters_section:
            characters_content = characters_section.group(1)
            
            # 匹配所有角色
            character_patterns = [
                r'<角色(\d+)>(.*?)</角色\1>',
                r'<主角(\d+)>(.*?)</主角\1>',
                r'<配角(\d+)>(.*?)</配角\1>'
            ]
            
            for pattern in character_patterns:
                character_matches = re.finditer(pattern, characters_content, re.DOTALL)
                for match in character_matches:
                    character_content = match.group(2)
                    character_info = {}
                    
                    # 提取角色信息
                    name_match = re.search(r'<姓名>(.*?)</姓名>', character_content)
                    if name_match:
                        character_info['name'] = name_match.group(1)
                    
                    gender_match = re.search(r'<性别>(.*?)</性别>', character_content)
                    if gender_match:
                        gender_value = gender_match.group(1)
                        character_info['gender'] = '男' if gender_value == 'Male' else '女' if gender_value == 'Female' else '其他'
                    
                    age_match = re.search(r'<年龄段>(.*?)</年龄段>', character_content)
                    if age_match:
                        age_value = age_match.group(1)
                        # 映射年龄段
                        age_mapping = {
                            '23-30_YoungAdult': '青年',
                            '31-45_MiddleAged': '中年',
                            '25-40_FantasyAdult': '青年',
                            '18-25_YoungAdult': '青年',
                            '46-60_MiddleAged': '中年',
                            '60+_Elder': '老年',
                            '12-18_Teen': '青少年',
                            '5-12_Child': '儿童'
                        }
                        character_info['age_group'] = age_mapping.get(age_value, '青年')
                    
                    role_num_match = re.search(r'<角色编号>(.*?)</角色编号>', character_content)
                    if role_num_match:
                        character_info['role_number'] = role_num_match.group(1)
                    
                    if character_info.get('name'):
                        result['characters'].append(character_info)
        
        # 提取分镜信息
        scene_pattern = r'<分镜(\d+)>(.*?)</分镜\1>'
        scene_matches = re.finditer(scene_pattern, narration_content, re.DOTALL)
        
        for scene_match in scene_matches:
            scene_number = scene_match.group(1)
            scene_content = scene_match.group(2)
            
            # 提取解说内容 - 先提取分镜级别的解说内容
            narration_match = re.search(r'<解说内容>(.*?)</解说内容>', scene_content, re.DOTALL)
            scene_narration = narration_match.group(1).strip() if narration_match else ''
            
            # 提取图片特写信息
            closeup_pattern = r'<图片特写(\d+)>(.*?)(?=<图片特写\d+>|$)'
            closeup_matches = re.finditer(closeup_pattern, scene_content, re.DOTALL)
            
            # 如果有解说内容但没有图片特写，创建一个默认的特写
            closeup_list = list(closeup_matches)
            if scene_narration and not closeup_list:
                # 创建模拟match对象
                class MockMatch:
                    def __init__(self, group1, group2):
                        self._group1 = group1
                        self._group2 = group2
                    def group(self, n):
                        return self._group1 if n == 1 else self._group2
                
                # 构造包含解说内容的默认特写
                full_content = f"<解说内容>{scene_narration}</解说内容><图片prompt></图片prompt>"
                closeup_list = [MockMatch('1', full_content)]
            
            closeup_matches = closeup_list
            
            # 处理图片特写内容
            for closeup_match in closeup_matches:
                closeup_number = closeup_match.group(1)
                closeup_content = closeup_match.group(2)
                
                # 提取特写人物信息 - 支持多种格式
                featured_character = ''
                
                # 方法1：查找<角色姓名>标签
                char_name_match = re.search(r'<角色姓名>(.*?)</角色姓名>', closeup_content)
                if char_name_match:
                    featured_character = char_name_match.group(1).strip()
                else:
                    # 方法2：查找<角色编号>标签
                    role_num_match = re.search(r'<角色编号>(.*?)</角色编号>', closeup_content)
                    if role_num_match:
                        role_number = role_num_match.group(1).strip()
                        # 根据角色编号找到对应的角色名称
                        for char in result['characters']:
                            if char.get('role_number') == role_number:
                                featured_character = char.get('name', '')
                                break
                        if not featured_character:
                            featured_character = role_number
                    else:
                        # 方法3：查找<特写人物>标签
                        featured_char_match = re.search(r'<特写人物>(.*?)(?:</特写人物>|<角色编号>|<角色姓名>)', closeup_content, re.DOTALL)
                        if featured_char_match:
                            char_content = featured_char_match.group(1).strip()
                            # 根据角色类型找到对应的角色名称
                            for char in result['characters']:
                                if char.get('role_number') == char_content:
                                    featured_character = char.get('name', '')
                                    break
                            if not featured_character:
                                featured_character = char_content
                
                # 提取解说内容 - 使用更宽松的匹配
                narration_match = re.search(r'<解说内容>(.*?)(?:</解说内容>|<图片prompt>|</图片特写|$)', closeup_content, re.DOTALL)
                narration_text = narration_match.group(1).strip() if narration_match else scene_narration
                
                # 提取图片prompt - 使用更宽松的匹配
                prompt_match = re.search(r'<图片prompt>(.*?)(?:</图片prompt>|</图片特写|$)', closeup_content, re.DOTALL)
                image_prompt = prompt_match.group(1).strip() if prompt_match else ''
                
                # 创建分镜记录
                narration_record = {
                    'scene_number': f"{scene_number}-{closeup_number}",
                    'featured_character': featured_character,
                    'narration': narration_text,
                    'image_prompt': image_prompt
                }
                
                result['narrations'].append(narration_record)
        
        return result
        
    except Exception as e:
        print(f"解析解说文案时出错: {str(e)}")
        return {
            'chapter_info': {},
            'characters': [],
            'narrations': []
        }