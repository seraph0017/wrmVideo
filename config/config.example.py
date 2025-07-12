# TTS配置示例
TTS_CONFIG = {
    "appid": "your_appid_here",
    "access_token": "your_access_token_here",
    "cluster": "volcano_tts",
    "voice_type": "BV701_streaming",
    "host": "openspeech.bytedance.com"
}

# Ark配置示例
ARK_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "your_api_key_here",
    "model": "doubao-seed-1.6-250615"  # 脚本生成使用的模型
}




STORY_STYLE = {
  "青春校园": {
    "core_style": "清新明亮、青春悸动、校园日常",
    "artist_reference": "竹冈美穗（《蜂蜜与四叶草》）",
    "model_prompt": "竹冈美穗风格 + 青春校园 + 清新色调",
    "render_prompt_guide": "需突出人物互动（同桌说笑/社团活动/放学路上），叠加浅蓝/淡粉等清新色调，突出阳光光影和少年少女的细腻表情"
  },
  "古风言情": {
    "core_style": "国风古韵、线条细腻、意境唯美",
    "artist_reference": ["夏达（《长歌行》）", "伊吹五月（插画）"],
    "model_prompt": ["夏达古风 + 典雅线条 + 国风意境", "伊吹五月国风 + 唯美插画 + 古韵氛围"],
    "render_prompt_guide": "需突出服饰细节（广袖襦裙/玉佩发簪），搭配水墨晕染质感，突出人物眉眼的婉约神态和场景的留白意境"
  },
  "玄幻修真": {
    "core_style": "奇幻宏大、特效华丽、仙魔世界观",
    "artist_reference": ["藤崎龙（《封神演义》）", "CLAMP（奇幻风格）"],
    "model_prompt": ["藤崎龙奇幻 + 仙侠场景 + 华丽特效", "CLAMP奇幻 + 仙魔世界观 + 梦幻光影"],
    "render_prompt_guide": "需突出奇幻元素（御剑飞行/法术特效/上古神兽），叠加流光溢彩的特效光效，突出人物法器的细节和场景的层次感"
  },
  "科幻未来": {
    "core_style": "机械硬核、赛博朋克、未来都市",
    "artist_reference": ["贰瓶勉（《BLAME!》）", "士郎正宗（《攻壳机动队》）"],
    "model_prompt": ["贰瓶勉科幻 + 机械结构 + 赛博朋克", "攻壳机动队风格 + 未来都市 + 冷硬质感"],
    "render_prompt_guide": "需突出科技元素（全息投影/金属机械臂/雨夜反光地面），搭配冷蓝/紫色调，突出机械细节的精密感和都市的疏离感"
  },
  "悬疑推理": {
    "core_style": "阴郁紧张、剧情压抑、细节致郁",
    "artist_reference": ["浦泽直树（《怪物》）", "出水ぽすか（《约定的梦幻岛》）"],
    "model_prompt": ["浦泽直树悬疑 + 阴暗氛围 + 写实线条", "约定的梦幻岛风格 + 推理剧情 + 压抑色调"],
    "render_prompt_guide": "需突出细节特写（颤抖的手/隐藏的线索/诡异的眼神），搭配暗灰/暗红低调色，突出阴影对比和人物的微表情张力"
  },
  "武侠江湖": {
    "core_style": "国风江湖、水墨张力、权谋侠义",
    "artist_reference": ["许先哲（《镖人》）", "郑问（水墨江湖）"],
    "model_prompt": ["许先哲武侠 + 大漠风沙 + 硬朗线条", "郑问水墨江湖 + 权谋侠义 + 水墨晕染"],
    "render_prompt_guide": "需突出武侠元素（刀剑交锋/披风飞扬/伤疤特写），叠加水墨笔触质感，突出人物动作的力量感和场景的苍茫感"
  },
  "恐怖惊悚": {
    "core_style": "诡异扭曲、心理致郁、视觉冲击",
    "artist_reference": ["伊藤润二（《富江》）", "楳图一雄（致郁风）"],
    "model_prompt": ["伊藤润二恐怖 + 扭曲人体 + 诡异氛围", "楳图一雄致郁风 + 惊悚剧情 + 暗黑色调"],
    "render_prompt_guide": "需突出扭曲细节（拉长的影子/非自然的肢体/空洞的眼神），搭配低饱和暗色调，突出画面的压迫感和生理不适感"
  },
  "恋爱甜宠": {
    "core_style": "甜美明亮、互动糖分、萌系人设",
    "artist_reference": ["高木直子（绘本）", "种村有菜（少女漫）"],
    "model_prompt": ["高木直子日常甜 + 恋爱互动 + 柔和色彩", "种村有菜少女漫 + 甜宠剧情 + 萌系人设"],
    "render_prompt_guide": "需捕捉甜蜜互动（牵手/对视/背后抱），搭配马卡龙色系，突出人物的红晕脸颊和肢体接触的柔软质感"
  },
  "治愈童话": {
    "core_style": "温暖治愈、自然奇幻、童真氛围",
    "artist_reference": "宫崎骏（吉卜力工作室）",
    "model_prompt": "宫崎骏治愈风 + 自然元素 + 柔和光影",
    "render_prompt_guide": "需突出奇幻生物（会说话的动物/小精灵），搭配暖黄/草绿等柔和色调，突出阳光透过树叶的光斑和人物与生物的友好互动"
  }
}