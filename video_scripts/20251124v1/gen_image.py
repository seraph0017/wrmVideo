#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_image.py - 根据narration.txt解析角色与场景，使用ComfyUI生成图片

目标：
- 复用 v3 的 narration 与角色解析、prompt 构建逻辑
- 参考 test/comfyui/test_image_compact.py 的请求流程
- 用解析出的完整prompt替换 image_compact.json 中正向提示（Positive Prompt）节点
- 生成图片并下载到对应章节目录，文件命名为 chapter_XXX_image_YY.jpeg

用法：
python video_scripts/20251124v1/gen_image.py data/001 \
  --api_url http://<HOST:PORT>/api/prompt \
  --workflow_json test/comfyui/image_compact.json \
  --poll_interval 1.0 --max_wait 300
  
# 单图片模式（重新生成指定场景）
python video_scripts/20251124v1/gen_image.py data/001/chapter_001 --scene 5
"""

import os
import sys
import re
import json
import time
import logging
from typing import Dict, List, Optional, Tuple

import requests

# 添加项目根目录到Python路径
# 当前文件路径: video_scripts/20251124v1/gen_image.py
# 项目根目录: video_scripts/20251124v1/gen_image.py -> ../../
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入配置
from config.config import COMFYUI_CONFIG

# ComfyUI 默认主机常量，可通过环境变量 COMFYUI_HOST 覆盖
COMFYUI_DEFAULT_HOST = os.getenv("COMFYUI_HOST", COMFYUI_CONFIG["default_host"])
DEFAULT_COMFYUI_PROMPT_URL = f"http://{COMFYUI_DEFAULT_HOST}/api/prompt"


# 日志配置
logs_dir = os.path.join(project_root, 'logs')
os.makedirs(logs_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'gen_image_async_v4.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NarrationParser:
    """narration.txt文件解析器（复用v3逻辑）"""

    def __init__(self, narration_file: str):
        self.narration_file = narration_file
        self.characters: Dict[str, Dict] = {}
        self.scenes: List[Dict] = []

    def parse_characters(self) -> Dict[str, Dict]:
        try:
            with open(self.narration_file, 'r', encoding='utf-8') as f:
                content = f.read()

            character_pattern = r'<角色\d+>(.*?)</角色\d+>'
            character_matches = re.findall(character_pattern, content, re.DOTALL)

            for match in character_matches:
                character_info = self._parse_single_character(match)
                if character_info and 'name' in character_info:
                    self.characters[character_info['name']] = character_info

            logger.info(f"解析到 {len(self.characters)} 个角色")
            return self.characters
        except Exception as e:
            logger.error(f"解析角色信息失败: {e}")
            return {}

    def _parse_single_character(self, character_text: str) -> Optional[Dict]:
        try:
            character_info: Dict[str, str] = {}

            name_match = re.search(r'<姓名>(.*?)</姓名>', character_text, re.DOTALL)
            if name_match:
                name_content = name_match.group(1).strip()
                nested_name_match = re.search(r'<角色姓名>(.*?)</角色姓名>', name_content)
                if nested_name_match:
                    character_info['name'] = nested_name_match.group(1).strip()
                else:
                    character_info['name'] = name_content

            gender_match = re.search(r'<性别>(.*?)</性别>', character_text)
            if gender_match:
                character_info['gender'] = gender_match.group(1).strip()

            age_match = re.search(r'<年龄段>(.*?)</年龄段>', character_text)
            if age_match:
                character_info['age'] = age_match.group(1).strip()

            appearance_match = re.search(r'<外貌特征>(.*?)</外貌特征>', character_text, re.DOTALL)
            if appearance_match:
                appearance_text = appearance_match.group(1)
                character_info['appearance'] = self._parse_appearance(appearance_text)

            clothing_match = re.search(r'<服装风格>(.*?)</服装风格>', character_text, re.DOTALL)
            if clothing_match:
                clothing_text = clothing_match.group(1)
                character_info['clothing'] = self._parse_clothing(clothing_text)

            return character_info
        except Exception as e:
            logger.error(f"解析单个角色信息失败: {e}")
            return None

    def _parse_appearance(self, appearance_text: str) -> Dict:
        appearance: Dict[str, str] = {}
        hair_style_match = re.search(r'<发型>(.*?)</发型>', appearance_text)
        if hair_style_match:
            appearance['hair_style'] = hair_style_match.group(1).strip()
        hair_color_match = re.search(r'<发色>(.*?)</发色>', appearance_text)
        if hair_color_match:
            appearance['hair_color'] = hair_color_match.group(1).strip()
        face_match = re.search(r'<面部特征>(.*?)</面部特征>', appearance_text)
        if face_match:
            appearance['face'] = face_match.group(1).strip()
        body_match = re.search(r'<身材特征>(.*?)</身材特征>', appearance_text)
        if body_match:
            appearance['body'] = body_match.group(1).strip()
        return appearance

    def _parse_clothing(self, clothing_text: str) -> Dict:
        clothing: Dict[str, str] = {}
        top_match = re.search(r'<上衣>(.*?)</上衣>', clothing_text)
        if top_match:
            clothing['top'] = top_match.group(1).strip()
        bottom_match = re.search(r'<下装>(.*?)</下装>', clothing_text)
        if bottom_match:
            clothing['bottom'] = bottom_match.group(1).strip()
        accessory_match = re.search(r'<配饰>(.*?)</配饰>', clothing_text)
        if accessory_match:
            clothing['accessory'] = accessory_match.group(1).strip()
        return clothing

    def parse_scenes(self) -> List[Dict]:
        try:
            with open(self.narration_file, 'r', encoding='utf-8') as f:
                content = f.read()

            scene_pattern = r'<分镜\d+>(.*?)</分镜\d+>'
            scene_matches = re.findall(scene_pattern, content, re.DOTALL)
            for scene_match in scene_matches:
                scene_shots = self._parse_scene_shots(scene_match)
                self.scenes.extend(scene_shots)
            logger.info(f"解析到 {len(self.scenes)} 个场景镜头")
            return self.scenes
        except Exception as e:
            logger.error(f"解析场景信息失败: {e}")
            return []

    def _parse_scene_shots(self, scene_text: str) -> List[Dict]:
        shots: List[Dict] = []
        shot_pattern = r'<图片特写\d+>(.*?)</图片特写\d+>'
        shot_matches = re.findall(shot_pattern, scene_text, re.DOTALL)
        for shot_match in shot_matches:
            shot_info = self._parse_single_shot(shot_match)
            if shot_info:
                shots.append(shot_info)
        return shots

    def _parse_single_shot(self, shot_text: str) -> Optional[Dict]:
        try:
            shot_info: Dict[str, str] = {}
            character_match = re.search(r'<角色姓名>(.*?)</角色姓名>', shot_text)
            if character_match:
                shot_info['character'] = character_match.group(1).strip()
            narration_match = re.search(r'<解说内容>(.*?)</解说内容>', shot_text)
            if narration_match:
                shot_info['narration'] = narration_match.group(1).strip()
            prompt_match = re.search(r'<图片prompt>(.*?)</图片prompt>', shot_text)
            if prompt_match:
                shot_info['scene_prompt'] = prompt_match.group(1).strip()
            return shot_info
        except Exception as e:
            logger.error(f"解析单个镜头信息失败: {e}")
            return None


class ImagePromptBuilder:
    """图片prompt构建器（写实风格）"""

    def __init__(self):
        self.style_prompt = (
            "画面风格是写实风格，注重真实感和细节表现，"
            "光影自然，色彩真实，人物造型符合真实人体比例，"
            "质感细腻，追求照片级的视觉效果"
        )

    def build_character_description(self, character_info: Dict, use_minimal: bool = False) -> str:
        """构建写实风格的人物描述
        
        Args:
            character_info: 角色信息字典
            use_minimal: 是否使用最小化描述（只包含基本外貌，不包含服装）
        """
        try:
            parts: List[str] = []
            
            # 性别和年龄描述（写实风格）
            if 'gender' in character_info:
                gender_desc = "男性" if character_info['gender'] == 'Male' else "女性"
                if 'age' in character_info:
                    age_info = character_info['age']
                    # 解析年龄段，如 "21-30_YoungAdult" 或 "31-45_MiddleAged"
                    if '_' in age_info:
                        age_range = age_info.split('_')[0]
                        parts.append(f"一位{age_range}岁的{gender_desc}")
                    else:
                        parts.append(f"一位{gender_desc}")
                else:
                    parts.append(f"一位{gender_desc}")
            
            # 外貌特征（写实风格描述）
            if 'appearance' in character_info:
                ap = character_info['appearance']
                
                # 面部特征
                if 'face' in ap:
                    face_desc = ap['face']
                    # 将漫画风格描述转换为写实描述
                    face_desc = face_desc.replace('眼神', '目光')
                    parts.append(f"面容{face_desc}")
                
                # 发型和发色
                if 'hair_style' in ap and 'hair_color' in ap:
                    hair_style = ap['hair_style']
                    hair_color = ap['hair_color']
                    parts.append(f"{hair_color}的{hair_style}")
                elif 'hair_style' in ap:
                    parts.append(f"{ap['hair_style']}")
                
                # 身材特征
                if 'body' in ap:
                    body_desc = ap['body']
                    # 将漫画风格描述转换为写实描述
                    body_desc = body_desc.replace('体态', '身形')
                    parts.append(body_desc)
            
            # 如果是最小化模式，跳过服装描述
            if not use_minimal:
                # 服装描述（仅在非最小化模式下添加）
                if 'clothing' in character_info:
                    cl = character_info['clothing']
                    clothing_parts = []
                    
                    if 'top' in cl:
                        top = cl['top']
                        # 过滤掉具体朝代服装描述
                        if not any(dynasty in top for dynasty in ['宋朝', '明朝', '清朝', '唐朝', '汉朝', '元朝', '秦朝', '圆领袍']):
                            # 添加材质和质感描述
                            if '丝质' in top or '绸' in top:
                                clothing_parts.append(f"{top}（质感细腻）")
                            elif '棉' in top or '麻' in top:
                                clothing_parts.append(f"{top}（质地自然）")
                            else:
                                clothing_parts.append(top)
                    
                    if 'bottom' in cl:
                        bottom = cl['bottom']
                        # 过滤掉具体朝代服装描述
                        if not any(dynasty in bottom for dynasty in ['宋朝', '明朝', '清朝', '唐朝', '汉朝', '元朝', '秦朝']):
                            clothing_parts.append(bottom)
                    
                    if 'accessory' in cl and cl['accessory'] not in ['无其他装饰', '无', '无其他饰品']:
                        accessory = cl['accessory']
                        clothing_parts.append(f"配有{accessory}")
                    
                    if clothing_parts:
                        parts.append(f"穿着{', '.join(clothing_parts)}")
            
            # 添加写实风格的补充描述
            result = "，".join(parts)
            if result:
                result += "，真实的光影效果，自然的皮肤质感，细腻的细节表现"
            
            return result
        except Exception as e:
            logger.error(f"构建角色描述失败: {e}")
            return ""

    def build_complete_prompt(self, character_info: Dict, scene_prompt: str) -> str:
        """构建完整的prompt，优先使用场景本身的描述
        
        策略：
        1. 使用最小化的角色描述（只包含基本外貌，不包含具体服装）
        2. 场景prompt中的描述优先级最高，保持原样
        3. 添加写实风格前缀
        """
        try:
            style_part = self.style_prompt
            # 使用最小化角色描述，避免覆盖场景中的服装描述
            character_part = self.build_character_description(character_info, use_minimal=True)
            scene_part = scene_prompt
            
            # 如果角色描述为空，直接使用风格+场景
            if not character_part:
                return f"{style_part}。{scene_part}"
            
            return f"{style_part}。{character_part}。{scene_part}"
        except Exception as e:
            logger.error(f"构建完整prompt失败: {e}")
            return scene_prompt


class ComfyUIClient:
    """ComfyUI API 客户端（参考 test_image_compact.py）"""

    def __init__(self, api_url: str, timeout: int = 30, max_retries: int = 3, retry_delay: int = 1):
        """
        初始化客户端并规范化工作流提交端点。

        端点兼容策略：
        - 支持传入以下形式：
          1) `http://host:port` → 归一到 `http://host:port/api/prompt`
          2) `http://host:port/api` → 归一到 `http://host:port/api/prompt`
          3) `http://host:port/api/prompt` → 原样使用
          4) `http://host:port/prompt` → 原样使用（部分部署只暴露 /prompt）
          5) 其他包含 `/api/...` 的路径 → 回到根并使用 `/api/prompt`

        同时准备一个备用端点 `/prompt`，在提交返回 404/405 时自动回退。
        """
        def normalize_prompt_url(url: str) -> str:
            base = (url or '').strip().rstrip('/')
            if not base:
                base = 'http://127.0.0.1:8188'
            # 已是标准 /api/prompt
            if base.endswith('/api/prompt') or '/api/prompt' in base:
                return base
            # 明确传入了 /prompt（不带 /api）
            if base.endswith('/prompt') or ('/prompt' in base and '/api' not in base):
                return base
            # 以 /api 结尾，补齐 /prompt
            if base.endswith('/api'):
                return base + '/prompt'
            # 包含 /api/... 的其他形式，回到根并统一到 /api/prompt
            if '/api' in base:
                return base.split('/api')[0].rstrip('/') + '/api/prompt'
            # 纯主机:端口形式，默认 /api/prompt
            return base + '/api/prompt'

        self.api_url = normalize_prompt_url(api_url)
        # 备用端点用于 404/405 回退：优先从根组装 /prompt
        root = self.api_url.rstrip('/')
        if '/api/prompt' in root:
            self._root = root.split('/api/prompt')[0]
        elif '/prompt' in root:
            self._root = root.split('/prompt')[0]
        else:
            self._root = root.split('/api')[0]
        self._fallback_prompt_url = self._root.rstrip('/') + '/prompt'
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _api_base(self) -> str:
        """返回以 `/api` 结尾的基础 API 前缀，用于 history/view/upload。

        兼容：当提交端点为 `/prompt` 时，history/view 仍使用 `/api/...` 路径。
        """
        url = self.api_url.rstrip('/')
        if '/api/prompt' in url:
            root = url.split('/api/prompt')[0]
        elif '/prompt' in url:
            root = url.split('/prompt')[0]
        else:
            root = url.split('/api')[0]
        return f"{root}/api"

    def _append_filename_query(self, url: str, filename: Optional[str]) -> str:
        """
        为URL追加 `image` 查询参数，用于 HAProxy/路由调试（不影响接口实际语义）。

        Args:
            url: 原始URL
            filename: 要追加的路由标识值（例如 `chapter_001_image_01.jpeg`）。若为空则返回原URL。

        Returns:
            str: 追加查询参数后的URL。
        """
        if not filename:
            return url
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            # 使用 image 作为路由标识参数键
            qs['image'] = [filename]
            new_query = urlencode(qs, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
        except Exception:
            sep = '&' if '?' in url else '?'
            return f"{url}{sep}image={filename}"

    def _append_query_param(self, url: str, key: str, value: Optional[str]) -> str:
        """
        为URL追加任意查询参数键值对，不改变已有参数，用于路由/调试。

        Args:
            url: 原始URL
            key: 要追加的查询参数键名
            value: 要追加的查询参数值；为空则返回原URL

        Returns:
            str: 追加查询参数后的URL
        """
        if not value:
            return url
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            qs[key] = [value]
            new_query = urlencode(qs, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
        except Exception:
            sep = '&' if '?' in url else '?'
            return f"{url}{sep}{key}={value}"

    def submit_workflow(self, workflow_payload: Dict[str, any], filename_param: Optional[str] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """提交工作流，自动处理端点 405/404 的回退。

        Args:
            workflow_payload: ComfyUI 工作流 JSON（将作为 `prompt` 字段提交）。
            filename_param: 可选，附加到提交端点的查询参数 `image`，用于后端路由标识。

        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: (提交是否成功, 响应JSON或文本, 错误信息)
        """
        payload = {"prompt": workflow_payload, "client_id": "python_client"}
        for attempt in range(self.max_retries):
            try:
                # 首选归一端点
                url_primary = self._append_filename_query(self.api_url, filename_param)
                resp = self.session.post(url_primary, json=payload, timeout=self.timeout)
                if resp.status_code == 200:
                    try:
                        return True, resp.json(), None
                    except json.JSONDecodeError:
                        return True, {"raw": resp.text}, None
                # 在 404/405 时尝试备用 /prompt
                if resp.status_code in (404, 405):
                    url_fallback = self._append_filename_query(self._fallback_prompt_url, filename_param)
                    logger.warning(f"提交端点返回 {resp.status_code}，尝试回退到 {url_fallback}")
                    resp2 = self.session.post(url_fallback, json=payload, timeout=self.timeout)
                    if resp2.status_code == 200:
                        try:
                            return True, resp2.json(), None
                        except json.JSONDecodeError:
                            return True, {"raw": resp2.text}, None
                    else:
                        err_fb = f"HTTP错误(回退): {resp2.status_code} - {resp2.text}"
                        logger.error(err_fb)
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        return False, None, err_fb
                # 其他非 200 的情况
                err = f"HTTP错误: {resp.status_code} - {resp.text}"
                logger.error(err)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False, None, err
            except requests.exceptions.Timeout:
                err = f"请求超时 (超过 {self.timeout} 秒)"
                logger.error(err)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False, None, err
            except requests.exceptions.ConnectionError:
                err = "连接错误：无法连接到 ComfyUI 服务器"
                logger.error(err)
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False, None, err
            except Exception as e:
                err = f"未知错误: {e}"
                logger.error(err)
                return False, None, err
        return False, None, "所有重试尝试都失败了"

    def wait_for_output_filename(self, prompt_id: str, poll_interval: float = 1.0, max_wait: int = 300, filename_param: Optional[str] = None):
        base_api = self._api_base()
        url = f"{base_api}/history/{prompt_id}"
        if filename_param:
            url = self._append_filename_query(url, filename_param)
        end_ts = time.time() + max_wait
        while time.time() < end_ts:
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except json.JSONDecodeError:
                        data = {}
                    obj = data
                    if isinstance(obj, dict):
                        if prompt_id in obj and isinstance(obj[prompt_id], dict):
                            obj = obj[prompt_id]
                        elif 'history' in obj and isinstance(obj['history'], dict):
                            obj = obj['history'].get(prompt_id) or next(iter(obj['history'].values()), {})
                    outputs = obj.get('outputs') if isinstance(obj, dict) else {}
                    if outputs:
                        for _, node_val in outputs.items():
                            images = node_val.get('images') if isinstance(node_val, dict) else None
                            if images:
                                for item in images:
                                    fname = item.get('filename')
                                    subfolder = item.get('subfolder', '')
                                    type_ = item.get('type', 'output')
                                    if fname:
                                        logger.info(f"获取到输出文件: {fname} (subfolder={subfolder}, type={type_})")
                                        return fname, subfolder, type_
                time.sleep(poll_interval)
            except requests.RequestException as e:
                logger.warning(f"轮询历史接口异常: {e}")
                time.sleep(poll_interval)
        logger.error("轮询等待超时，未获取到输出文件名")
        return None, None, None

    def download_view_file_as(self, filename: str, subfolder: str, type_: str, save_dir: str, save_as: str, filename_param: Optional[str] = None) -> Optional[str]:
        """
        从 /api/view 下载指定文件，并保存为给定文件名。

        功能描述：
        - 构造 `/api/view` 下载 URL，包含实际文件定位所需的 `filename`、`type`、`subfolder` 参数。
        - 追加路由/调试用途的查询参数 `image=<chapter_xxx_image_xx.jpeg>`，用于在代理层标识目标输出名，不影响真实文件下载。

        参数说明：
        - filename: ComfyUI 生成的真实文件名（如 `ComfyUI_00067_.png`）。
        - subfolder: 子目录名称（空字符串表示根目录）。
        - type_: 文件类型（通常为 `output`）。
        - save_dir: 本地保存目录路径。
        - save_as: 本地保存的目标文件名（如 `chapter_002_image_01.jpeg`）。
        - filename_param: 路由标识值，将以 `image` 参数附加到下载 URL。

        返回值：
        - 成功返回本地保存的完整路径；失败返回 None。
        """
        base_api = self._api_base()
        params = f"filename={filename}&type={type_}" + (f"&subfolder={subfolder}" if subfolder else "")
        url = f"{base_api}/view?{params}"
        # 追加用于路由/调试的请求级标识，不影响真实 filename
        url = self._append_query_param(url, 'image', filename_param)
        try:
            resp = self.session.get(url, stream=True, timeout=self.timeout)
            if resp.status_code == 200:
                os.makedirs(save_dir, exist_ok=True)
                local_path = os.path.join(save_dir, save_as)
                with open(local_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"文件已下载到: {local_path}")
                return local_path
            else:
                logger.error(f"下载失败，状态码: {resp.status_code}")
                return None
        except requests.RequestException as e:
            logger.error(f"下载异常: {e}")
            return None


def load_workflow_json(path: str) -> Dict:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"工作流JSON不存在: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def set_positive_prompt(workflow: Dict, prompt_text: str) -> Dict:
    """将workflow中的正向提示词替换为prompt_text（优先使用_meta.title辨识Positive节点）"""
    try:
        # 深拷贝以避免副作用
        import copy
        wf = copy.deepcopy(workflow)

        # 尝试根据 _meta.title 包含 'Positive Prompt' 的 CLIPTextEncode 节点识别
        positive_node_id = None
        for node_id, node in wf.items():
            if isinstance(node, dict) and node.get('class_type') == 'CLIPTextEncode':
                meta = node.get('_meta', {})
                title = meta.get('title', '')
                if 'Positive' in title:
                    positive_node_id = node_id
                    break

        # 回退到固定节点ID '12'
        if positive_node_id is None and '12' in wf and wf['12'].get('class_type') == 'CLIPTextEncode':
            positive_node_id = '12'

        if positive_node_id is None:
            logger.warning("未找到正向提示节点，跳过替换")
            return wf

        wf[positive_node_id]['inputs']['text'] = prompt_text
        return wf
    except Exception as e:
        logger.error(f"替换正向提示失败: {e}")
        return workflow


def is_chapter_directory(path: str) -> bool:
    if not os.path.isdir(path):
        return False
    dir_name = os.path.basename(path)
    if not dir_name.startswith('chapter_'):
        return False
    narration_file = os.path.join(path, 'narration.txt')
    return os.path.exists(narration_file)


def find_chapter_directories(data_dir: str) -> List[str]:
    chapter_dirs: List[str] = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if is_chapter_directory(item_path):
            chapter_dirs.append(item_path)
    return sorted(chapter_dirs)


def save_prompt_info(prompt: str, output_path: str, workflow_name: str, scene_number: int) -> None:
    try:
        from datetime import datetime
        prompt_path = os.path.splitext(output_path)[0] + '.prompt.json'
        info = {
            "image_file": os.path.basename(output_path),
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "workflow": workflow_name,
            "scene_number": scene_number
        }
        with open(prompt_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Prompt信息已保存到: {prompt_path}")
    except Exception as e:
        logger.warning(f"保存Prompt信息失败: {e}")


def process_chapter_with_comfyui(chapter_dir: str, client: ComfyUIClient, workflow_template: Dict, poll_interval: float, max_wait: int, delay_between_requests: float = 1.0, scene_number: Optional[int] = None) -> int:
    try:
        narration_file = os.path.join(chapter_dir, 'narration.txt')
        if not os.path.exists(narration_file):
            logger.warning(f"narration.txt文件不存在: {narration_file}")
            return 0

        logger.info(f"开始处理章节: {chapter_dir}")
        parser = NarrationParser(narration_file)
        characters = parser.parse_characters()
        scenes = parser.parse_scenes()
        if not characters or not scenes:
            logger.warning(f"章节 {chapter_dir} 没有找到角色或场景信息")
            return 0

        prompt_builder = ImagePromptBuilder()
        chapter_name = os.path.basename(chapter_dir)

        success_count = 0
        
        # 如果指定了scene_number，只处理该场景
        if scene_number is not None:
            logger.info(f"单图片模式：只生成场景 {scene_number}")
            scenes_to_process = [(scene_number, scenes[scene_number - 1])] if scene_number <= len(scenes) else []
            if not scenes_to_process:
                logger.error(f"场景编号 {scene_number} 超出范围 (总共 {len(scenes)} 个场景)")
                return 0
        else:
            scenes_to_process = enumerate(scenes, 1)
        
        for i, scene in scenes_to_process:
            if 'character' not in scene or 'scene_prompt' not in scene:
                logger.warning(f"场景 {i} 缺少必要信息，跳过")
                continue
            character_name = scene['character']
            if character_name not in characters:
                logger.warning(f"角色 {character_name} 信息未找到，跳过场景 {i}")
                continue

            character_info = characters[character_name]
            complete_prompt = prompt_builder.build_complete_prompt(character_info, scene['scene_prompt'])

            output_filename = f"{chapter_name}_image_{i:02d}.jpeg"
            output_path = os.path.join(chapter_dir, output_filename)
            
            # 单图片模式下，即使文件存在也要重新生成
            if os.path.exists(output_path) and scene_number is None:
                logger.info(f"图片已存在，跳过: {output_path}")
                success_count += 1
                continue

            # 替换正向提示词
            wf = set_positive_prompt(workflow_template, complete_prompt)

            # 提交工作流
            # 提交工作流，附带 filename 查询参数用于路由
            ok, res, err = client.submit_workflow(wf, filename_param=output_filename)
            if not ok:
                logger.error(f"工作流提交失败: {err}")
                continue

            prompt_id = None
            if isinstance(res, dict):
                prompt_id = res.get('prompt_id') or (res.get('data') or {}).get('prompt_id')
            if not prompt_id:
                logger.error(f"未获取到 prompt_id，响应: {res}")
                continue

            logger.info(f"prompt_id: {prompt_id}")

            # 轮询输出文件名
            filename, subfolder, type_ = client.wait_for_output_filename(prompt_id, poll_interval=poll_interval, max_wait=max_wait, filename_param=output_filename)
            if not filename:
                logger.error(f"场景 {i} 未获取到输出文件")
                continue

            # 下载并重命名到章节目录
            saved = client.download_view_file_as(
                filename,
                subfolder or '',
                type_ or 'output',
                save_dir=chapter_dir,
                save_as=output_filename,
                filename_param=output_filename
            )
            if not saved:
                logger.error(f"场景 {i} 下载失败")
                continue

            # 保存prompt信息
            save_prompt_info(complete_prompt, output_path, workflow_name=os.path.basename('test/comfyui/image_compact.json'), scene_number=i)
            success_count += 1
            logger.info(f"✓ 场景 {i} 图片生成成功: {output_path}")

            if delay_between_requests > 0:
                time.sleep(delay_between_requests)

        logger.info(f"章节 {chapter_dir} 处理完成，成功生成 {success_count}/{len(scenes)} 张图片")
        return success_count
    except Exception as e:
        logger.error(f"处理章节失败: {e}")
        return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="使用ComfyUI生成章节图片")
    parser.add_argument('input_path', help='数据目录(如 data/001) 或单个章节目录(如 data/001/chapter_001)')
    parser.add_argument('--api_url', default=f"http://{COMFYUI_CONFIG['default_host']}/api/prompt", help='ComfyUI api/prompt 地址')
    parser.add_argument('--workflow_json', default=os.path.join('test', 'comfyui', 'image_compact.json'), help='工作流JSON模板路径')
    parser.add_argument('--timeout', type=int, default=COMFYUI_CONFIG.get('timeout', 30), help='请求超时(秒)')
    parser.add_argument('--max_retries', type=int, default=3, help='提交重试次数')
    parser.add_argument('--poll_interval', type=float, default=COMFYUI_CONFIG.get('poll_interval', 1.0), help='轮询history间隔(秒)')
    parser.add_argument('--max_wait', type=int, default=600, help='轮询最长等待(秒)，默认600秒(10分钟)')
    parser.add_argument('--delay', type=float, default=1.0, help='每次生成之间的延迟(秒)')
    parser.add_argument('--scene', type=int, help='指定生成单个场景编号（单图片模式）')

    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        logger.error(f"路径不存在: {args.input_path}")
        sys.exit(1)

    # 初始化客户端与工作流模板
    client = ComfyUIClient(api_url=args.api_url, timeout=args.timeout, max_retries=args.max_retries)
    workflow_template = load_workflow_json(args.workflow_json)
    logger.info(f"加载工作流模板: {args.workflow_json}")
    logger.info(f"ComfyUI API 地址: {args.api_url}")
    
    if args.scene is not None:
        logger.info(f"单图片模式：将生成场景 {args.scene}")

    # 单章节或数据目录
    if is_chapter_directory(args.input_path):
        process_chapter_with_comfyui(args.input_path, client, workflow_template, poll_interval=args.poll_interval, max_wait=args.max_wait, delay_between_requests=args.delay, scene_number=args.scene)
    else:
        # 遍历数据目录下的所有章节
        chapter_dirs = find_chapter_directories(args.input_path)
        if not chapter_dirs:
            logger.warning(f"在 {args.input_path} 中没有找到章节目录")
            logger.info("请确保每个章节目录包含 narration.txt 文件")
            sys.exit(0)
        
        # 单图片模式不支持多章节
        if args.scene is not None:
            logger.error("单图片模式（--scene）只能用于单个章节目录，不支持数据目录")
            sys.exit(1)
        
        total_success = 0
        for i, chapter_dir in enumerate(chapter_dirs, 1):
            logger.info(f"处理章节 {i}/{len(chapter_dirs)}: {chapter_dir}")
            total_success += process_chapter_with_comfyui(chapter_dir, client, workflow_template, poll_interval=args.poll_interval, max_wait=args.max_wait, delay_between_requests=args.delay)
            if i < len(chapter_dirs):
                time.sleep(1)
        logger.info(f"所有章节处理完成，总共成功生成 {total_success} 张图片")


if __name__ == '__main__':
    main()

