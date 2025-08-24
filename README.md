# 🎬 AI视频生成系统

一个基于AI的自动化视频生成系统，能够将小说文本转换为带有解说、图片和字幕的视频内容。系统集成了豆包大模型、火山引擎TTS和图像生成服务，实现从文本到视频的全自动化流程。

## ✨ 最新更新

- 🔧 **图片重新生成修复**: 修复auto-regenerate模式的跳过生成问题：
  - **问题修复**: 移除了重新生成函数中的文件存在性检查
  - **强制替换**: 确保检测失败的图片能够被强制重新生成和替换
  - **逻辑优化**: generate_image_with_character_to_chapter_async函数专用于重新生成失败图片
  - **用户体验**: 避免"图片已存在，跳过生成"导致失败图片无法被替换的问题
- 🔇 **音效配置优化**: 移除风声和水声音效以改善视频体验：
  - **风声移除**: 注释掉"风"关键词对应的wind_gentle.wav和wind_strong.wav音效
  - **水声移除**: 注释掉"水"关键词对应的water_splash.wav音效
  - **山风移除**: 注释掉"山"关键词对应的mountain_wind.wav音效
  - **流水移除**: 注释掉"流水"关键词对应的water_flowing.wav音效
  - **体验优化**: 避免风声和水声音效干扰语音解说的清晰度
  - **保留其他**: 保留铃声、脚步声、战斗音效等不冲突的音效
  - **时间段保障**: 强化narration_01的6-10秒音效保障，确保该时间段必有音效
  - **备选机制**: 添加音效文件不存在时的备选方案，使用铃声作为后备音效
- 🔍 **图片检测标准强化**: 进一步严格化图片质量检测要求：
  - **脖子暴露检测**: 将脖子暴露检测标准提升为严格模式，即使很小的暴露也不允许
  - **检测描述强化**: 在检测提示词中明确"脖子必须完全被服装遮盖"的要求
  - **重新生成优化**: 更新重新生成提示词，强调"脖子必须完全被服装遮盖不能有任何暴露"
  - **双重覆盖**: 同时更新llm_image.py和llm_narration_image.py两个检测脚本
  - **质量提升**: 确保生成的角色图片和旁白图片都符合更严格的审查标准
- 📝 **字幕断句逻辑优化**: 改进ASS字幕生成中的文本分割算法：
  - **句子完整性**: 优先按句子进行分割，确保每句话尽量完整地在一行显示
  - **智能分割**: 首先按句号、感叹号、问号等主要标点符号分割句子
  - **次级分割**: 对于过长的句子，按逗号、顿号等次级标点进一步分割
  - **自然断开**: 新增智能断开算法，为过长句子选择最自然的断开位置
  - **断开优先级**: 定义了15种自然断开点的优先级，从逗号到连词等
  - **词语保护**: 在必要的词语级分割中，确保不从词语中间断开
  - **避免碎片**: 不再从句子中间或词语中间随意断开，提升字幕可读性
  - **长度控制**: 严格控制每行字符数不超过设定限制，同时保持自然性
- 🎵 **音频生成速度优化**: 调整gen_audio.py中的语音生成速度为1.2倍速：
  - **语速提升**: 将默认语音生成速度从1.0倍调整为1.2倍，提高语音播放效率
  - **时长优化**: 在保持语音清晰度的前提下，缩短音频时长，提升观看体验
  - **参数配置**: 通过speed_ratio=1.2参数实现语速控制，确保语音质量不受影响
  - **全局应用**: 所有解说音频都将以1.2倍速生成，统一提升播放节奏
- 🔍 **图片检测逻辑修复**: 修复llm_narration_image.py中的判断逻辑错误：
  - **逻辑优化**: 修复LLM分析结果判断逻辑，优先检查"失败"关键词，避免误判
  - **问题解决**: 解决了LLM返回"失败"结果却显示"✓ 检查通过"的bug
  - **准确识别**: 现在能正确识别包含"领口通过标准"等短语的失败结果
  - **自动重新生成**: 修复检查失败时的重新生成逻辑，确保所有失败图片都能被记录并触发重新生成
  - **结果可靠**: 确保图片质量检测结果的准确性，提高内容审核效果
- 🔄 **异步任务监控优化**: 优化check_async_tasks.py脚本，默认启用持续监控模式：
  - **默认常驻模式**: 直接执行`python check_async_tasks.py`即默认启用`--process-all --monitor`功能，持续监控所有数据目录
  - **智能监控**: 自动扫描data目录下所有00x/chapter_xxx结构，持续处理异步图片生成任务
  - **不退出运行**: 脚本持续运行，每30秒检查一次所有异步任务状态，自动下载完成的图片
  - **向下兼容**: 保留所有原有参数选项，添加`--legacy-mode`参数进入交互模式
  - **错误恢复**: 监控过程中遇到错误会自动重试，确保服务稳定性
  - **实时统计**: 每轮检查后显示处理统计信息，包括章节数、任务数、成功率等
- 📁 **项目目录整理**: 完成项目目录结构优化，提升代码组织和维护性：
  - **测试文件统一**: 将所有测试文件移动到test目录，包括test_character_image_matching.py、test_character_parsing.py、test_dynamic_characters.py等
  - **目录结构清理**: 清理根目录下的测试文件，保持项目根目录整洁
  - **文档更新**: 同步更新README.md文档，反映最新的项目结构
  - **便于维护**: 统一的测试文件管理，便于开发和测试工作
- 📹 **视频文件大小优化**: 全面优化视频编码参数，确保最终生成的视频文件大小控制在50MB以下：
  - **多级压缩策略**: 在concat_first_video.py、concat_narration_video.py和concat_finish_video.py中优化编码参数
  - **GPU加速编码**: 支持NVIDIA GPU (h264_nvenc)、macOS VideoToolbox和CPU (libx264)多种编码方式
  - **智能比特率控制**: 根据不同硬件平台调整CQ/CRF值（32）和最大比特率限制
  - **最终压缩机制**: 在concat_finish_video.py中新增compress_final_video()函数，对超过50MB的视频进行二次压缩
  - **质量保证**: 保持720x1280分辨率和30fps帧率，确保视频质量的同时大幅减小文件大小
  - **自动检测压缩**: 生成完成后自动检测文件大小，超过50MB时自动触发最终压缩
  - **压缩效果显著**: 测试显示可将136MB文件压缩至17-31MB，在保持良好视频质量的同时确保文件大小控制在50MB以内
- 🔊 **音频标准化优化**: 修复视频中不同narration段之间音量不一致的问题：
  - **动态音频标准化**: 在concat_finish_video.py中使用dynaudnorm滤镜自动平衡音频音量
  - **解决音量突变**: 修复不同narration段之间音量差异导致的声音突然变小问题
  - **智能音量控制**: 自动调整音频动态范围，确保整个视频音量保持一致
  - **保持音质**: 在标准化过程中保持音频质量和清晰度，避免音质损失
- 🖼️ **角标图片尺寸优化**: 调整rmxs.png角标图片尺寸以匹配视频分辨率：
  - **尺寸标准化**: 将src/banner/rmxs.png从1080x1920调整为720x1280，与视频分辨率完全匹配
  - **智能缩放**: 在concat_narration_video.py中添加水印缩放逻辑，将720x1280的水印缩放到360x640（1/2大小）
  - **尺寸优化**: 经过测试调整，从最初的180x320（1/4大小）调整为360x640（1/2大小），确保角标既不会过小也不会覆盖视频
  - **解决显示问题**: 修复角标大小不一致和底部角标显示不完整的问题，避免水印覆盖整个视频
  - **保持质量**: 使用FFmpeg高质量缩放算法，确保角标图片清晰度
  - **完美适配**: 角标以合适的大小显示在视频右上角，不影响主要内容的观看
- 🖼️ **图片格式检测优化**: 优化gen_first_video_async.py中的图片格式识别机制，基于文件实际内容而非扩展名判断格式：
  - **内容检测**: 使用imghdr模块和文件头检测技术，准确识别图片的真实格式
  - **MIME类型映射**: 支持JPEG、PNG、GIF、BMP、WebP等主流图片格式的准确识别
  - **扩展名容错**: 解决扩展名与实际格式不符的问题（如.jpeg文件实际为PNG格式）
  - **向下兼容**: 保持对现有代码的完全兼容，仅优化格式检测逻辑
  - **测试验证**: 提供test_image_format_detection.py测试脚本，验证各种格式混淆场景
  - **错误处理**: 增强错误处理机制，对无法识别的格式提供合理的默认值
- 🎭 **角色解析功能升级**: 全面升级gen_character_image.py中的角色解析功能，支持新格式动态角色标签：
  - **动态角色识别**: 支持新格式 `<角色1>`、`<角色2>` 等动态角色标签，不再限制于固定的四个角色
  - **向下兼容**: 保持对旧格式 `<主角1>`、`<配角1>` 的完全兼容，确保现有项目正常运行
  - **增强解析能力**: 新增对 `<特殊标记>` 字段的解析，更完整地提取角色特征信息
  - **智能过滤**: 自动过滤 "无" 值的配饰和特殊标记，避免无效信息干扰图片生成
  - **测试验证**: 提供 `test_character_parsing.py` 测试脚本，验证角色解析功能的准确性
  - **灵活扩展**: 支持任意数量的角色定义，适应不同小说的角色设定需求
- 📁 **异步任务目录优化**: 优化llm_image.py中的异步任务管理，将任务文件保存到各个chapter的async_tasks目录：
  - **分布式任务管理**: 新增 `generate_image_with_character_to_chapter_async()` 函数，将异步任务保存到对应chapter的async_tasks子目录
  - **智能路径解析**: 自动解析图片路径，识别对应的chapter目录（如data/004/chapter_001）
  - **目录自动创建**: 自动创建chapter下的async_tasks目录，无需手动管理
  - **任务信息完整**: 保存完整的任务信息，包括task_id、输出路径、提示词、角色图片等
  - **重新生成优化**: 修改 `regenerate_failed_image()` 函数，使用新的分布式任务管理机制
  - **测试工具**: 新增 `test_chapter_async_tasks.py` 测试脚本，验证分布式任务管理功能
  - **便于管理**: 每个chapter的异步任务独立管理，便于追踪和调试
- 🔍 **图片领口审查优化**: 全面优化llm_image.py中的领口审查prompt，提升交领等问题领口的识别准确性：
  - **详细审查标准**: 明确定义通过和失败的领口类型，包括圆领、立领、高领等通过类型
  - **重点识别交领**: 特别强调交领/衽领的识别，明确其"左右衣襟交叉重叠，形成V字形开口"的特征
  - **皮肤露出检测**: 重点关注领口是否露出脖子以下皮肤区域，提升检测精度
  - **传统服装适配**: 针对汉服、古装等传统服装的交领设计进行专门优化
  - **结构化prompt**: 采用清晰的标准分类和判断要求，提升LLM理解准确性
  - **测试工具**: 新增test_optimized_prompt.py测试脚本，便于验证prompt优化效果
  - **自动重新生成**: 支持--auto-regenerate参数，检测到失败图片时自动重新生成
- 🚀 **增强版脚本生成器 gen_script_v2.py**: 基于gen_script.py的全面增强版本，新增多项高级功能：
  - **自动章节质量验证**: 生成完成后自动验证所有章节的解说文案质量（长度、内容完整性等）
  - **智能重新生成**: 对不达标章节自动重新生成，支持最多3次重试，确保所有章节质量达标
  - **指定章节数量生成**: 支持 `--limit N` 参数，可指定只生成前N个章节（如前5章、前10章）
  - **智能验证机制**: 仅验证字数范围（1200-1800字），自动修复XML标签闭合问题，无需重新生成
  - **模板化Prompt**: 使用chapter_narration_prompt.j2模板文件生成解说内容，便于维护和调整
  - **智能目录结构**: 根据小说文件路径自动确定输出目录（如data/004/xxx.txt输出到data/004）
  - **内存优化处理**: 采用分批处理和即时保存策略，生成内容后立即保存到文件并释放内存，避免大量数据在内存中积累
  - **验证模式**: 支持 `--validate-only` 仅验证现有章节，不生成新内容
  - **重新生成模式**: 支持 `--regenerate` 重新生成无效章节
  - **灵活配置**: 支持自定义最小/最大长度、最大重试次数等参数
  - **详细日志**: 提供完整的生成、验证、重试过程日志，便于问题排查
  - **命令行友好**: 丰富的命令行参数支持，适合自动化脚本和批处理
- 🧪 **图片生成Prompt测试工具**: 新增专门的图片生成prompt测试脚本，便于调试和优化图片生成效果：
  - **多种预设prompt**: 提供5种不同类型的测试prompt（基础男性、神秘女性、西式骑士、科幻战士、简化测试）
  - **6种测试模式**: 单个预设测试、批量预设测试、自定义prompt测试、预设prompt批量比较、自定义prompt专业测试、退出
  - **增强的自定义prompt功能**: 支持多行prompt输入（输入END结束）、可自定义生成数量（1-20张）、自动保存prompt内容到文件、支持prompt命名和分类管理
  - **批量比较功能**: 同一prompt可生成1-20张图片进行效果对比，推荐生成10张比较一致性和质量
  - **结果管理**: 自动创建带时间戳的输出目录，便于管理测试结果
  - **详细日志**: 显示完整的prompt内容和生成过程，便于调试
  - **成功率统计**: 批量测试时提供成功率统计，评估prompt质量
  - **基于原版**: 基于batch_generate_character_images.py，保持API调用的一致性
- 📝 **字幕断句语义优化**: 全面优化gen_ass.py中的字幕断句逻辑，确保语义完整性：
  - **语义模式识别**: 新增 `semantic_patterns` 列表，定义语义紧密相关的词汇模式
  - **智能分词**: 集成 `jieba` 分词库，提供更准确的中文分词支持
  - **语义合并**: 新增 `_merge_semantic_words()` 函数，自动合并语义相关的词汇
  - **完整性检测**: 新增 `_is_semantic_incomplete()` 函数，检测语义不完整的分割
  - **段落优化**: 重构 `_optimize_segments()` 函数，综合考虑长度和语义完整性
  - **成对符号**: 增强成对符号检测，确保引号、括号等不被分割
  - **避免截断**: 有效避免"一句话没说完"或"两句话被截断"的问题
  - **时间戳修正**: 保持原有的时间戳重叠修正和索引安全检查功能
- 🎵 **第一视频音效匹配功能**: 为gen_first_video_async.py添加完整的音效匹配和处理功能：
  - **音效匹配**: 新增 `find_sound_effect()` 函数，根据narration文本内容智能匹配音效
  - **音效管理**: 新增 `get_sound_effects_for_first_video()` 函数，为第一个视频生成音效列表
  - **铃声特效**: 第一个章节（chapter_001）前5秒自动添加铃声音效（音量0.5）
  - **智能匹配**: 根据narration内容匹配相应音效（脚步声、门声、战斗音效等）
  - **默认音效**: 无匹配音效时自动添加默认脚步声，避免视频过于单调
  - **音效保存**: 将音效信息保存为sound_effects.json文件，供后续视频合成使用
  - **时间控制**: 合理安排音效时间，避免铃声与其他音效重叠
  - **音量统一**: 所有音效音量统一设置为0.5，与concat_narration_video.py保持一致
- 🔊 **BGM和音效音量优化**: 调整背景音乐和音效音量，避免覆盖字幕和旁白：
  - **BGM音量调整**: 将concat_finish_video.py中的BGM音量从0.15进一步降低到0.1
  - **音效音量调整**: 将concat_narration_video.py中所有音效音量从0.1-0.15大幅提升到0.5
  - **铃声音量**: narration1开头铃声音量从0.15调整为0.5
  - **脚步声音量**: 默认脚步声音量从0.1调整为0.5
  - **对话音效**: 所有对话匹配音效音量从0.1调整为0.5
  - **音频平衡**: BGM进一步降低以确保不干扰主要内容，音效音量提升以增强视频表现力
- 🔄 **Regenerated图片替换功能**: 提供完整的图片重新生成和替换解决方案：
  - **失败图片解析**: 自动解析 `fail.txt` 文件，识别需要重新生成的图片
  - **批量重新生成**: 支持批量提交图片重新生成任务，自动生成增强描述文本
  - **智能替换**: 一键替换Character_Images目录下的所有regenerated图片
  - **安全备份**: 替换前自动备份原始图片，确保数据安全
  - **任务追踪**: 完整的异步任务状态查询和结果下载功能
  - **清理工具**: 提供regenerated文件和备份文件的清理脚本
  - **测试验证**: 包含完整的测试脚本，验证所有核心功能
- 🚀 **火山云L4 GPU支持**: 全面支持火山云L4 GPU环境的FFmpeg配置和优化：
  - **L4 GPU检测**: 自动识别NVIDIA L4 GPU并应用专门的优化配置
  - **专用配置**: L4 GPU使用p4预设、VBR码率控制、空间/时间自适应量化等优化参数
  - **编译脚本**: 提供`test_volcano_l4_ffmpeg.py`脚本，支持L4环境检测、性能测试和编译脚本生成
  - **Docker支持**: 生成针对L4 GPU优化的Docker配置和运行命令
  - **生产环境**: 完整的L4 GPU生产环境配置指南和自动化部署脚本
  - **性能优化**: 针对L4 GPU的NVENC编码器进行专门优化，提升编码效率和质量
- 🛠️ **subprocess编码问题修复**: 全面修复FFmpeg和其他子进程调用中的UTF-8解码错误：
  - **编码安全**: 将所有 `subprocess.run` 调用的 `text=True` 改为 `text=False`，以字节模式处理输出
  - **安全解码**: 为所有 `stderr` 和 `stdout` 使用添加安全解码逻辑，使用 `errors='ignore'` 忽略无法解码的字符
  - **全面覆盖**: 修复了 `concat_narration_video.py`、`concat_first_video.py`、`concat_finish_video.py`、`gen_video.py`、`gen_script.py` 等主要文件
  - **测试文件**: 同时修复了 `test/` 目录下的所有相关测试文件
  - **错误解决**: 彻底解决了 "'utf-8' codec can't decode byte 0xb7" 等编码错误
  - **GPU检测**: 修复GPU检测失败时的编码问题，确保错误信息正确显示
- 🔧 **解说内容验证功能优化**: 全面改进验证功能的准确性和用户体验：
  - **精确提取**: 新增 `extract_narration_content()` 函数，只提取 `<解说内容>` 标签内的文本进行验证
  - **避免误判**: 解决了之前将整个 narration.txt 文件当作解说文案验证的问题
  - **准确验证**: 现在只验证实际的解说文案内容，而不包括角色信息、图片描述等其他内容
  - **验证逻辑优化**: 使用正则表达式提取所有解说内容，将多个分镜的解说内容合并后进行长度验证
  - **分类处理**: 重构验证结果分类，区分长度不足和其他问题的章节
  - **交互优化**: 支持选择性重新生成不同类型的问题章节，提升用户体验
  - **错误处理修复**: 修复 EOFError 处理，为所有 `input()` 调用添加异常处理，避免管道输入时程序崩溃
  - **单章节验证**: 新增 `_validate_single_chapter()` 函数，支持单个章节目录验证
- 🔄 **脚本生成重试机制**: 为gen_script.py添加智能重试和质量验证机制：
  - **质量验证**: 自动检查生成的解说文案长度和内容质量（800-1500字）
  - **智能重试**: 对不符合要求的章节自动重新生成，最多重试3次
  - **全流程验证**: 生成完成后遍历所有章节，确保每个narration文件都符合要求
  - **最终检查**: 重新生成后进行最终验证，确保所有章节质量达标
  - **详细日志**: 提供详细的验证和重试过程日志，便于问题排查
- 🛠️ **FFmpeg字幕路径转义修复**: 修复字幕文件路径中特殊字符导致的滤镜解析错误：
  - **路径转义**: 自动转义字幕文件路径中的冒号和反斜杠等特殊字符
  - **兼容性提升**: 确保在不同操作系统和路径格式下的字幕正常显示
  - **错误预防**: 避免"No option name"和"Error parsing filterchain"等FFmpeg错误
  - **稳定性增强**: 提升视频生成流程的整体稳定性
- 🔧 **nvenc编码器检测改进**: 增强GPU硬件加速的可靠性检测：
  - **智能检测**: 不仅检测GPU驱动，还实际测试nvenc编码器是否可用
  - **自动回退**: 当nvenc不可用时（如驱动版本过低）自动回退到CPU编码
  - **错误提示**: 提供详细的错误信息，帮助用户了解GPU不可用的原因
  - **全面覆盖**: 同步更新所有视频处理脚本的GPU检测逻辑
- 🛠️ **CUDA兼容性修复**: 修复NVIDIA GPU硬件加速与FFmpeg滤镜的兼容性问题：
  - **问题解决**: 移除hwaccel_output_format参数，避免CUDA格式与scale滤镜不兼容
  - **稳定性提升**: 确保GPU加速在使用复杂滤镜链时的稳定性
  - **全面修复**: 同步修复concat_first_video.py、concat_finish_video.py、concat_narration_video.py三个文件
- 🐳 **Docker环境GPU支持**: 增强Docker环境下NVIDIA GPU硬件加速的兼容性：
  - **Docker检测**: 新增Docker环境检测，支持通过环境变量和文件系统检测容器环境
  - **GPU环境变量**: 支持检测NVIDIA_VISIBLE_DEVICES和CUDA_VISIBLE_DEVICES环境变量
  - **驱动文件检测**: 检测/proc/driver/nvidia/version文件确认GPU驱动可用性
  - **全面兼容**: 同步更新concat_first_video.py、concat_narration_video.py、concat_finish_video.py三个文件
  - **测试工具**: 新增test_docker_ffmpeg.py脚本，提供Docker环境FFmpeg配置检测和优化建议
  - **运行建议**: 自动生成Docker运行命令建议，包括GPU设备映射和环境变量配置
- 🔄 **gen_audio.py简化**: 移除多线程、多进程、多协程相关代码，改为简单的顺序执行方式：
  - **简化架构**: 去除ThreadPoolExecutor和threading模块依赖
  - **顺序处理**: 按章节和解说段落顺序生成语音文件
  - **清晰日志**: 简化输出信息，移除线程相关标识
  - **稳定性提升**: 避免并发处理可能导致的资源竞争和错误
- 🚀 **FFmpeg参数优化**: 全面优化视频编码参数以提升合成速度，在保证输出标准的前提下：
  - **NVIDIA GPU**: 使用更快的预设(p2)和低延迟调优(ll)，减少前瞻帧数和B帧数量
  - **CPU编码**: 使用fast预设，优化运动估计和参考帧设置，显著提升编码速度
  - **智能检测**: 自动检测GPU环境并应用相应的优化参数
- 🔄 **gen_video.py 重构**: 彻底重写 `gen_video.py` 脚本，现在作为流程编排器，按顺序执行 `concat_first_video.py`、`concat_narration_video.py` 和 `concat_finish_video.py`，实现模块化的视频生成流程
- 🎵 **音频混合优化**: 修复 `concat_finish_video.py` 中BGM盖住原有narration音频的问题，使用FFmpeg的amix滤镜将原有音频（音量1.0）与BGM（音量0.3）进行混合，确保解说声音清晰可听
- 📊 **统计逻辑优化**: 优化语音生成统计逻辑，添加文件存在检查和跳过机制，统计结果更准确
- 🛠️ **错误处理改进**: 改进语音生成错误处理，增加详细错误信息显示，提升调试体验
- 🔊 **语音生成优化**: 优化语音生成日志输出，移除详细API响应日志（包含phone、start_time、end_time等字段），减少终端输出冗余信息
- 📁 **文件重命名**: 将 `gen_video_async.py` 重命名为 `gen_first_video_async.py`，更好地反映其功能定位
- 🎯 **图片生成规则优化**: 每个章节固定生成30张图片（10个分镜×3张图片），确保视频内容的一致性
- 🔄 **智能生成策略**: 先尝试API生成图片，失败后自动从Character_Images目录复制补足
- 🛡️ **图片生成保障**: 精确任务统计和智能重试机制，确保所有图片都能成功生成
- 🔄 **智能重试系统**: 自动检测失败任务并重试，支持单独重试失败任务
- 📊 **任务状态管理**: 完成的任务自动移动到done_tasks目录，保持任务目录整洁
- 🔧 **完整工作流**: 从任务提交到图片下载的完整自动化流程
- 📈 **实时监控**: 提供任务状态监控和自动下载功能
- 🔄 **同步/异步双模式**: 支持同步和异步两种图片生成模式
- 📁 **目录结构优化**: Character_Images目录移至根目录，便于管理
- 🎨 **角色图片系统**: 完整的五层角色图片目录结构（性别/年龄/风格/文化/气质）
- ⚡ **性能优化**: 改进的图片生成和视频合成流程

## 🚀 功能特性

### 核心功能
- **🤖 智能文本处理**: 自动将长篇小说分割成适合的章节，支持大文本智能分块
- **📝 AI解说生成**: 使用豆包模型生成详细的解说文案，支持多种开场风格
- **🎨 图片自动生成**: 根据文本内容生成配套图片，支持720x1280竖屏格式
- **🎵 语音合成**: 将解说文案转换为自然语音，支持多种音色
- **🎬 视频合成**: 自动合成图片、音频和字幕为完整视频
- **📺 智能字幕系统**: 自动字幕生成、居中对齐、透明背景、智能断句

### 高级特性
- **⚡ 批量处理**: 支持批量生成多个章节视频
- **🎯 智能断句**: 优化字幕显示效果，支持换行后居中对齐
- **🔧 多格式支持**: 支持多种音频和视频格式
- **⚙️ 配置灵活**: 可自定义各种生成参数
- **🛡️ 内容规避**: 自动规避敏感内容，确保合规性
- **🎪 多种开场**: 支持热开场、前提开场、冷开场等多种风格
- **🎨 多种艺术风格**: 支持漫画、写实、水彩、油画四种图片生成风格

### 最新优化功能
- **📖 智能断句功能**: 根据标点符号和语义进行智能断句，提升观看体验
- **🖼️ 多音频共图**: 多个音频文件可共用一张图片，提高资源利用效率
- **🎨 字体样式优化**: 字幕居中对齐、透明背景、去除首尾标点符号
- **⚡ 性能提升**: 优化处理流程，提升生成速度和稳定性
- **📺 单行字幕显示**: 优化字幕生成逻辑，确保视频中只显示单行字幕，避免多行字幕影响观看体验

- **🧠 智能字幕处理**: 自动截取过长文本并添加省略号，移除换行符，确保字幕简洁易读

## 📁 项目结构

```
wrmVideo/
├── .gitignore
├── README.md               # 项目说明（包含完整功能介绍和优化总结）
├── main.md                 # 主要使用说明
├── config/                 # 配置目录
│   └── prompt_config.py   # Prompt配置管理
├── data/                   # 数据存储目录
│   ├── 001/                # 项目数据目录
│   │   ├── chapter01/      # 章节目录
│   │   │   ├── chapter01_script.txt  # 章节脚本
│   │   │   ├── *.mp3       # 生成的音频文件
│   │   │   ├── *.jpeg      # 生成的图片文件
│   │   │   ├── *.mp4       # 生成的视频片段
│   │   │   └── chapter01_complete.mp4  # 完整章节视频
│   │   └── final_complete_video.mp4    # 最终合并视频
│   └── test1/              # 测试数据目录
├── test/                   # 测试文件目录
│   ├── test_*.py           # 各种测试脚本
│   ├── debug_*.py          # 调试脚本
│   ├── test_character_image_matching.py # 角色图片匹配测试
│   ├── test_character_parsing.py # 角色解析测试
│   ├── test_dynamic_characters.py # 动态角色测试
│   ├── test_json_fix.py    # JSON修复测试
│   ├── test_videotoolbox.py # VideoToolbox测试
│   ├── test_voice_debug.py # 语音调试测试
│   ├── test_voice_direct.py # 语音直接测试
│   ├── test_concat.txt     # 合并测试文本
│   └── test_server_ffmpeg.py # 服务器FFmpeg配置检测脚本
├── Character_Images/       # 角色图片库（已移至根目录）
├── src/                    # 源代码目录
│   ├── core/               # 核心模块
│   ├── bgm/                # 背景音乐
│   └── sound_effects/      # 音效库
└── utils/                  # 工具模块
├── async_tasks/            # 异步任务目录（进行中的任务）
├── done_tasks/             # 已完成任务目录（自动移动）
├── generate.py             # 主程序入口
├── gen_image.py            # 同步图片生成脚本
├── gen_image_async.py      # 异步图片生成脚本（支持统计、重试和失败任务处理）
├── check_and_retry_images.py  # 图片任务检查和重试脚本
├── check_async_tasks.py    # 异步任务状态查询和下载脚本
├── generate_all_images.py  # 完整图片生成流程脚本
├── gen_script.py           # 解说文案生成脚本
├── gen_script_v2.py        # 增强版解说文案生成脚本（支持章节质量验证、重新生成、指定章节数量）
├── gen_audio.py            # 音频生成脚本
├── gen_first_video_async.py # 第一个narration视频生成脚本（异步生成video_1和video_2）
├── concat_first_video.py   # 合并video_1与video_2并加入转场特效脚本
├── concat_narration_video.py # 生成主视频（添加旁白、BGM、音效等）
├── concat_finish_video.py  # 生成完整视频（添加片尾视频）
├── gen_video.py            # 视频生成流程编排器（依次执行上述三个脚本）
├── upload_tos.py           # TOS存储服务上传脚本
├── llm_image.py            # LLM图片分析工具（批量检查Character_Images目录图片的人物着装领口类型）
├── requirements.txt        # 项目依赖

### 核心脚本说明

#### 图片生成相关

- **`gen_image.py`**: 同步图片生成，适合小批量处理
- **`gen_image_async.py`**: 异步图片生成脚本，新增功能：
  - 自动统计所有narration文件中的图片特写数量
  - 逐一发起请求并存储响应到async_tasks目录
  - 自动检查并重试失败任务，确保所有任务都返回task_id
  - 支持`--retry-failed`参数单独重试失败任务
- **`check_async_tasks.py`**: 异步任务状态查询和下载脚本：
  - 检查任务状态并下载完成的图片
  - 自动将下载成功的任务文件移动到done_tasks目录
  - 支持单次检查和持续监控模式
- **`check_and_retry_images.py`**: 图片生成检查和重试脚本（旧版本）
- **`generate_all_images.py`**: 完整的图片生成流程，集成任务提交、监控和重试


├── test/                   # 测试脚本目录
│   ├── test_audio.py      # 音频测试
│   ├── test_chapter.txt
│   ├── test_chapter_split.py # 章节分割测试
│   ├── test_chapters/
│   ├── test_generate_modes.py # 生成模式测试脚本
│   ├── test_long_text.py  # 长文本处理测试
│   ├── test_optimized_features.py
│   ├── test_output_new.txt
│   ├── test_small.txt
│   ├── test_split.py      # 文本分割测试
│   ├── test_subtitle.py   # 字幕相关测试
│   ├── test_subtitle_fix.py
│   ├── test_subtitle_improvements.py
│   ├── check_character_images_count.py # 角色图片目录文件数量检查脚本
│   └── generate_missing_images_report.py # 缺失图片详细报告生成脚本
└── utils/                  # 工具脚本目录
    ├── demo_styles.py     # 艺术风格演示脚本
    ├── fix_audio_quality.py # 音频质量修复工具
    └── init.py            # 初始化清理脚本
```

## 🔧 环境要求

- **Python**: 3.6 或更高版本
- **FFmpeg**: 用于视频处理（需要系统安装）
- **火山引擎账号**: 用于TTS和图像生成服务
- **豆包API**: 用于AI文案生成
- **网络连接**: 稳定的网络环境

## 📦 安装依赖

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 安装FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
下载FFmpeg并添加到系统PATH中

### 3. Docker环境部署（推荐用于线上环境）

#### 基础Docker运行
```bash
# 基本运行命令（仅CPU）
docker run -it --rm \
  -v /path/to/your/project:/workspace \
  -w /workspace \
  your-ffmpeg-image:latest
```

#### NVIDIA GPU支持
```bash
# 使用NVIDIA GPU硬件加速（推荐）
docker run -it --rm \
  --gpus all \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,video,utility \
  -v /path/to/your/project:/workspace \
  -w /workspace \
  your-ffmpeg-image:latest

# 或使用nvidia-docker（旧版本）
nvidia-docker run -it --rm \
  -v /path/to/your/project:/workspace \
  -w /workspace \
  your-ffmpeg-image:latest
```

#### Docker环境检测
```bash
# 检测Docker环境中的FFmpeg和GPU配置
python test/test_docker_ffmpeg.py

# 该脚本会自动：
# - 检测Docker环境和NVIDIA运行时
# - 测试FFmpeg和NVENC编码器
# - 生成优化的Docker运行命令建议
```

#### Docker镜像要求
确保Docker镜像包含以下组件：
- **FFmpeg**: 支持NVENC编码器（如果使用GPU）
- **Python 3.6+**: 运行环境
- **NVIDIA驱动**: GPU支持（通过宿主机映射）

## ⚙️ 配置设置

### 1. 创建配置文件
```bash
cp config/config.example.py config/config.py
```

### 2. 配置API密钥
编辑 `config/config.py` 文件，填入你的API密钥：

```python
# TTS语音合成配置
TTS_CONFIG = {
    "appid": "your_appid_here",           # 火山引擎应用ID
    "access_token": "your_access_token",  # 访问令牌
    "cluster": "volcano_tts",             # 集群名称
    "voice_type": "BV701_streaming",      # 音色类型
    "host": "openspeech.bytedance.com"    # 服务地址
}

# AI模型配置（豆包）
ARK_CONFIG = {
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "api_key": "your_api_key_here"        # 豆包API密钥
}

# 图片生成配置
IMAGE_CONFIG = {
    "default_style": "manga",  # 默认艺术风格: manga, realistic, watercolor, oil_painting
    "size": "720x1280",       # 图片尺寸（竖屏格式）
    "watermark": False,       # 是否添加水印
    "model": "doubao-seedream-3-0-t2i-250415"  # 使用的图像生成模型
}

# TOS存储配置（从config.py的IMAGE_TWO_CONFIG中读取）
# TOS配置已集成到config.py文件中，使用上海区域
# endpoint: tos-cn-shanghai.volces.com
# region: cn-shanghai
```

### 3. 获取API密钥
- **火山引擎TTS**: 访问[火山引擎控制台](https://console.volcengine.com/)获取
- **豆包API**: 访问[豆包开放平台](https://www.volcengine.com/product/doubao)获取
- **TOS存储服务**: 访问[火山引擎TOS控制台](https://console.volcengine.com/tos)获取访问密钥

### 4. TOS存储配置说明
TOS上传功能的配置已集成到 `config/config.py` 文件中：

- **访问密钥**: 从 `IMAGE_TWO_CONFIG` 中的 `access_key` 和 `secret_key` 读取
- **服务区域**: 使用上海区域 (`tos-cn-shanghai.volces.com`)
- **无需额外配置**: 如果您已经配置了图片生成功能，TOS上传功能即可直接使用

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置API密钥
cp config/config.example.py config/config.py
# 编辑 config/config.py，填入你的API密钥
```

### 2. 配置化系统

项目现在支持基于Jinja2模板的配置化系统，所有prompt和配置都可以通过模板进行管理：

#### 配置文件说明
- `config/prompt_config.py`: 主配置管理文件
- `src/pic/pic_generation.j2`: 图片生成prompt模板
- `src/script/script_generation.j2`: 脚本生成prompt模板
- `src/voice/voice_config.j2`: 语音配置模板

#### 使用新的配置化模块
```python
from config.prompt_config import prompt_config, ART_STYLES, VOICE_PRESETS

# 图片生成
from src.pic.gen_pic import generate_image_with_style
generate_image_with_style("一个美丽的古代城市", style="manga")

# 语音生成
from src.voice.gen_voice import VoiceGenerator
generator = VoiceGenerator()
generator.generate_voice("测试文本", "output.mp3", preset="default")

# 脚本生成
from src.script.gen_script import ScriptGenerator
script_gen = ScriptGenerator()
script_gen.generate_script("小说内容", "output_dir")
```

### 2. 基本使用

#### 完整流程（推荐）
```bash
# 处理整个小说项目
python generate.py data/001

# 处理单个章节
python generate.py data/001/chapter_001
```

#### 分步骤处理
```bash
# 1. 生成解说文案
# 基础版本
python gen_script.py data/001

# 增强版本（推荐）- 支持质量验证和重新生成
python gen_script_v2.py novel.txt --output data/001 --chapters 50

# 只生成前5个章节
python gen_script_v2.py novel.txt --output data/001 --limit 5

# 仅验证现有章节质量
python gen_script_v2.py novel.txt --output data/001 --validate-only

# 验证并重新生成无效章节
python gen_script_v2.py novel.txt --output data/001 --validate-only --regenerate

# 自定义验证参数
python gen_script_v2.py novel.txt --output data/001 --min-length 1000 --max-length 1800 --max-retries 5

# 2. 生成图片（推荐使用异步模式）
# 推荐方式 - 异步生成（每个章节固定30张图片：10个分镜×3张图片）
python gen_image_async.py data/001

# 单个章节生成
python gen_image_async.py data/001/chapter_001

# 单独重试失败任务
python gen_image_async.py data/001 --retry-failed

# 任务监控和下载
python check_async_tasks.py --check-once

# 持续监控直到所有任务完成
python check_async_tasks.py --monitor

# 其他选项：
# 同步生成（简单直接）
python gen_image.py data/001

# 完整流程脚本
python generate_all_images.py data/001

# 3. 生成第一个narration的视频（异步生成 video_1 和 video_2）
python gen_first_video_async.py data/001

# 检查异步视频任务状态
python check_async_tasks.py --check-once

# 4. 合并 video_1 和 video_2（加入转场特效）
python concat_first_video.py data/001

# 5. 生成音频
python gen_audio.py data/001

# 6. 生成字幕文件
python gen_ass.py data/001

# 7. 执行完整视频生成流程（推荐）
python gen_video.py data/001

# 或者分步执行：
# 7a. 合并 video_1 和 video_2（加入转场特效）
python concat_first_video.py data/001

# 7b. 生成主视频（添加旁白、BGM、音效等）
python concat_narration_video.py data/001

# 7c. 生成完整视频（添加片尾视频）
python concat_finish_video.py data/001

# 8. 上传完整视频到TOS存储服务
# 基本用法（自动推导TOS路径）
python upload_tos.py data/002

# 自定义bucket和路径前缀
python upload_tos.py data/002 --bucket rm-tos-001 --prefix data002

# 查看帮助信息
python upload_tos.py --help

# 9. LLM图片分析（检查Character_Images目录下图片的人物着装领口类型）
# 基本用法（检查默认目录）
python llm_image.py

# 检查指定目录
python llm_image.py --directory /path/to/images

# 自定义检查提示词
python llm_image.py --prompt "自定义检查提示词"

# 限制检查图片数量
python llm_image.py --max-images 10

# 从指定图片开始处理（续传功能）
python llm_image.py --start-from "/Users/xunan/Projects/wrmVideo/Character_Images/Male/23-30_YoungAdult/SciFi/Chinese/Mysterious/YoungAdult_SciFi_Chinese_Mysterious_04.jpeg"

# 组合使用多个参数
python llm_image.py --start-from "/path/to/start/image.jpg" --max-images 100

# 10. 服务器FFmpeg配置检测（检查线上服务器的FFmpeg配置和GPU编码支持）
# 检测服务器FFmpeg配置
python test/test_server_ffmpeg.py

# 该脚本会检测：
# - FFmpeg版本和配置信息
# - NVIDIA GPU和驱动支持
# - 硬件编码器支持（h264_nvenc、hevc_nvenc、h264_videotoolbox等）
# - 必需的滤镜支持（subtitles、overlay、scale、amix等）
# - 实际编码器测试（NVENC和CPU编码）
# - 性能优化建议和配置推荐

# 11. Docker环境FFmpeg配置检测（专用于Docker容器环境）
# 检测Docker环境中的FFmpeg和GPU配置
python test/test_docker_ffmpeg.py

# 该脚本会检测：
# - Docker环境识别（通过/.dockerenv文件和环境变量）
# - NVIDIA Docker运行时支持
# - GPU设备映射和环境变量配置
# - FFmpeg版本和NVENC编码器支持
# - 生成Docker运行命令建议和配置优化建议

# 12. Character_Images目录文件完整性检查
# 快速检查所有角色图片目录的文件数量
python test/check_character_images_count.py

# 生成详细的缺失图片报告（包含CSV和文本格式）
python test/generate_missing_images_report.py

# 该脚本会检查：
# - 扫描Character_Images目录下所有最下级子目录
# - 检查每个目录是否包含完整的8个图片文件
# - 识别缺失的图片编号（01-08）
# - 生成详细的CSV和文本格式报告
# - 按缺失数量分组统计不完整的目录
# - 提供完整的目录结构和文件状态信息
```

### 3. 图片生成规则

系统采用固定的图片生成规则，确保视频内容的一致性：

- **每个章节固定30张图片**：10个分镜 × 3张图片
- **智能生成策略**：
  1. 首先尝试通过API生成图片
  2. 如果API生成失败，自动从Character_Images目录复制图片补足
- **图片命名规则**：`chapter_XXX_image_YY_Z.jpeg`
  - `XXX`：章节编号（如001）
  - `YY`：分镜编号（01-10）
  - `Z`：该分镜下的图片编号（1-3）

### 4. 图片生成模式选择

#### 同步模式（推荐用于调试）
```bash
# 实时生成，立即返回结果
python gen_image.py data/001/chapter_001
```

#### 异步模式（推荐用于批量处理）
```bash
# 提交任务到队列，适合大批量处理
python gen_image_async.py data/001

# 检查异步任务状态
python check_async_tasks.py
```

### 5. 角色图片系统

系统支持基于角色属性的智能图片选择：

```
Character_Images/
├── Male/Female              # 性别
│   ├── 15-22_Youth          # 年龄段
│   │   ├── Ancient/Fantasy  # 风格
│   │   │   ├── Chinese/Western  # 文化
│   │   │   │   ├── Common/Royal # 气质
│   │   │   │   │   └── *.jpg    # 角色图片
```

#### 批量生成角色图片
```bash
# 生成所有角色类型的图片
python batch_generate_character_images.py

# 异步批量生成
python batch_generate_character_images_async.py
```

## 📋 核心功能说明

### 🤖 解说文案生成
- **智能分块**: 自动处理长文本，支持大型小说
- **多种开场**: 热开场、前提开场、冷开场
- **内容规避**: 自动规避敏感内容，确保合规
- **格式化输出**: 结构化XML格式，便于后续处理

### 🎨 AI图像生成
- **双模式支持**: 同步模式（实时）+ 异步模式（批量）
- **图片生成保障**: 智能重试机制确保每张图片都生成成功
  - 自动检测失败任务并重试
  - 支持最大重试次数配置
  - 实时任务状态监控
  - 完整的进度报告和错误日志
- **角色图片系统**: 基于属性的智能角色图片选择
- **高质量输出**: 720x1280竖屏格式，适合短视频
- **风格多样**: 支持古风、现代、奇幻、科幻等多种风格

### 🎵 语音合成
- **高质量TTS**: 火山引擎TTS服务，自然流畅
- **时间戳支持**: 精确的字符级时间戳信息
- **多种音色**: 支持不同性别和年龄的音色
- **参数可调**: 语速、音量、音调等参数可自定义

### 🎬 视频合成
- **智能字幕**: 自动居中对齐、透明背景、智能断句
- **高质量编码**: H.264视频编码，AAC音频编码
- **自动同步**: 音频、图片、字幕完美同步
- **音频混合**: 智能混合原有narration音频与BGM，确保解说声音清晰（原音频音量1.0，BGM音量0.3）
- **章节拼接**: 支持将多个narration视频按顺序拼接，自动添加随机BGM和片尾视频

### 📤 TOS存储上传
- **批量上传**: 自动遍历章节目录，上传所有完整视频文件
- **智能路径**: 自动推导TOS存储路径，支持自定义前缀
- **进度监控**: 实时显示上传进度和状态
- **错误处理**: 完善的错误处理和重试机制
- **配置集成**: 直接使用config.py中的配置，无需额外设置
- **上海区域**: 使用火山引擎上海区域服务，提升上传速度

### 🔍 LLM图片分析
- **领口检查**: 专门检查人物着装领口类型（圆领、立领、高领 vs V领）
- **批量分析**: 自动遍历指定目录下的所有图片文件
- **续传功能**: 支持从指定图片开始处理，避免重复分析已处理的图片
- **多格式支持**: 支持jpg、jpeg、png、gif、bmp、webp等常见图片格式
- **Base64编码**: 使用base64编码处理图片，兼容性更好
- **自定义提示**: 支持自定义分析提示词，灵活控制分析内容
- **失败记录**: 自动将检测失败的图片路径和失败原因实时记录到data目录的fail.txt文件
- **智能记录**: 从头开始时清空失败记录文件，续传时追加记录
- **进度反馈**: 实时显示分析进度和结果，支持全局索引显示
- **Token统计**: 实时显示每次请求的token使用情况，包含输入、输出和总计token数
- **错误处理**: 完善的错误处理机制，跳过无法处理的图片
- **配置集成**: 直接使用config.py中的ARK_CONFIG配置，无需设置环境变量

## ⚠️ 注意事项

### 安全相关
1. **API密钥安全**: 请妥善保管API密钥，不要将其提交到版本控制系统
2. **配置文件**: `config.py` 文件已被添加到 `.gitignore` 中
3. **内容合规**: 系统已内置内容规避机制，确保生成内容合规

### 性能相关
1. **网络连接**: 确保网络连接稳定，API调用需要访问外部服务
2. **文件大小**: 长文本会自动分块处理，避免单次请求过大
3. **资源占用**: 视频生成过程会占用较多CPU和内存资源

### 兼容性
1. **Python版本**: 建议使用Python 3.8+以获得最佳兼容性
2. **FFmpeg版本**: 确保FFmpeg版本支持H.264编码
3. **依赖版本**: 建议使用最新版本的依赖包

## 🔧 故障排除

### 常见问题

#### 1. 环境问题
```bash
# 重新安装依赖
pip install -r requirements.txt --upgrade

# 检查FFmpeg安装
ffmpeg -version
```

#### 2. API相关
- **API调用失败**: 检查网络连接和API密钥配置
- **配额不足**: 确认API配额是否充足
- **权限错误**: 验证API密钥权限设置

#### 3. 文件处理
- **路径错误**: 确保输入文件路径正确
- **权限问题**: 检查输出目录写入权限
- **编码问题**: 确认文本文件为UTF-8编码

#### 4. 异步任务
```bash
# 检查异步任务状态
python check_async_tasks.py

# 查看任务详情
ls async_tasks/
```

#### 5. Docker环境问题
```bash
# 检查Docker环境配置
python test/test_docker_ffmpeg.py

# 常见Docker问题解决：

# 问题1: GPU不可用
# 解决: 确保使用正确的Docker运行参数
docker run --gpus all -e NVIDIA_VISIBLE_DEVICES=all ...

# 问题2: NVENC编码器不可用
# 解决: 检查FFmpeg是否支持NVENC
ffmpeg -encoders | grep nvenc

# 问题3: 权限问题
# 解决: 确保容器有足够权限访问GPU设备
# 检查宿主机NVIDIA驱动
nvidia-smi

# 问题4: 环境变量缺失
# 解决: 设置必要的NVIDIA环境变量
-e NVIDIA_DRIVER_CAPABILITIES=compute,video,utility
```

#### 6. GPU硬件加速问题
```bash
# 检查GPU状态
nvidia-smi

# 测试NVENC编码器
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 -c:v h264_nvenc -f null -

# 检查FFmpeg GPU支持
ffmpeg -hwaccels
ffmpeg -encoders | grep nvenc

# 常见GPU问题：
# - 驱动版本过低：更新NVIDIA驱动
# - FFmpeg不支持NVENC：重新编译FFmpeg或使用支持的版本
# - Docker环境GPU映射失败：检查Docker GPU运行时配置
```

### 错误代码
- `401`: API密钥错误或过期
- `403`: 权限不足或配额用尽
- `500`: 服务器内部错误
- `FileNotFoundError`: 文件路径错误

## 🛠️ 技术架构

### 核心技术栈
- **AI模型**: 豆包大模型（文案生成、图像生成）
- **语音合成**: 火山引擎TTS
- **视频处理**: FFmpeg
- **异步处理**: 任务队列系统

### 关键特性

#### 🎯 智能处理
- **智能断句**: 基于标点符号和语义的断句算法
- **角色识别**: 自动识别角色属性并匹配图片
- **内容规避**: 自动检测和规避敏感内容

#### ⚡ 性能优化
- **异步处理**: 支持大批量任务的异步处理
- **资源复用**: 图片资源智能复用机制
- **缓存机制**: 减少重复API调用

#### 🎨 视觉效果
- **高质量输出**: 720x1280竖屏格式
- **智能字幕**: 居中对齐、透明背景
- **多种风格**: 古风、现代、奇幻、科幻等

## 👨‍💻 开发说明

### 项目架构

```
核心流程:
文本输入 → 智能分割 → AI文案生成 → 图片生成 → 语音合成 → 字幕处理 → 视频合成
```

### 主要模块

- `generate.py`: 主程序入口，协调各模块工作
- `gen_script.py`: AI解说文案生成
- `gen_image.py` / `gen_image_async.py`: 图片生成（同步/异步）
- `gen_first_video_async.py`: 第一个narration视频生成（异步生成video_1和video_2）
- `gen_audio.py`: TTS语音合成
- `gen_video.py`: 视频生成流程编排器，按顺序执行三个阶段的视频处理
- `concat_first_video.py`: 第一阶段 - 合并video_1与video_2并加入转场特效
- `concat_narration_video.py`: 第二阶段 - 生成主视频（添加旁白、BGM、音效等）
- `concat_finish_video.py`: 第三阶段 - 生成完整视频（添加片尾视频）
- `upload_tos.py`: TOS存储服务上传工具，批量上传完整视频文件
- `llm_image.py`: LLM图片分析工具，批量检查Character_Images目录下图片的人物着装领口类型，自动记录检测失败的图片路径和失败原因到根目录

### 扩展开发

#### 自定义配置
```python
# 在config/config.py中修改配置
IMAGE_CONFIG = {
    "default_style": "your_style",
    "size": "720x1280",
    # ... 其他配置
}
```

#### 测试
```bash
# 运行测试
python test/test_integration.py
python test/test_character_images.py
```

## 🚀 火山云L4 GPU配置指南

### 环境检测和配置

#### 1. 环境检测
```bash
# 检测当前L4 GPU环境
python test/test_volcano_l4_ffmpeg.py

# 生成优化配置
python test/test_volcano_l4_ffmpeg.py --optimize

# 生成编译脚本
python test/test_volcano_l4_ffmpeg.py --compile

# 生成Docker配置
python test/test_volcano_l4_ffmpeg.py --docker

# 生成所有配置
python test/test_volcano_l4_ffmpeg.py --all
```

#### 2. L4 GPU优化配置

**自动检测**: 系统会自动检测L4 GPU并应用以下优化配置：
- **预设**: p4（L4 GPU最佳平衡预设）
- **码率控制**: VBR（可变比特率）
- **质量**: CQ 23（恒定质量）
- **自适应量化**: 空间和时间自适应量化
- **前瞻帧数**: 20帧
- **编码表面**: 32个

#### 3. 生产环境部署

**方式一：直接编译**
```bash
# 运行自动生成的编译脚本
bash l4_ffmpeg_compile.sh
```

**方式二：Docker部署**
```bash
# 构建L4优化的FFmpeg镜像
docker build -t ffmpeg-l4:latest -f Dockerfile.l4 .

# 运行容器（GPU支持）
docker run --gpus all -v /workspace:/workspace ffmpeg-l4:latest
```

#### 4. 性能验证
```bash
# 测试NVENC编码性能
ffmpeg -f lavfi -i testsrc2=duration=10:size=1920x1080:rate=30 \
  -c:v h264_nvenc -preset p4 -rc vbr -cq 23 \
  -spatial_aq 1 -temporal_aq 1 -rc-lookahead 20 \
  test_l4.mp4
```

### L4 GPU特性

- **计算能力**: 8.9（Ada Lovelace架构）
- **NVENC会话**: 支持多路并发编码
- **编码格式**: H.264/H.265 NVENC
- **解码加速**: NVDEC硬件解码
- **内存**: 24GB GDDR6

### 📋 完整依赖清单

详细的L4 GPU环境配置和依赖安装指南，请参考：
- **[L4 GPU依赖清单](L4_GPU_DEPENDENCIES.md)** - 包含系统依赖、CUDA环境、FFmpeg编译、Python包等完整配置指南

该文档包含：
- 🔧 NVIDIA驱动和CUDA环境配置
- 📦 FFmpeg编译依赖和优化配置
- 🐍 Python环境和包依赖
- 🐳 Docker环境配置
- ✅ 环境验证和性能测试
- 🚨 常见问题解决方案

### 🔍 快速环境检查

使用我们提供的依赖检查脚本快速验证您的L4 GPU环境：

```bash
# 基本检查
python test/check_l4_dependencies.py

# 详细检查（包含性能测试）
python test/check_l4_dependencies.py --performance

# 显示详细输出
python test/check_l4_dependencies.py --verbose
```

该脚本会自动检查：
- ✅ 系统环境（操作系统、Python版本）
- ✅ NVIDIA GPU 和驱动（L4 GPU检测）
- ✅ CUDA 环境和工具链
- ✅ FFmpeg 和 NVENC 编码器
- ✅ Python 包依赖
- ✅ 项目目录结构
- ✅ API 配置文件
- ✅ L4 GPU 性能测试（可选）

## 🔄 重新生成失败图片

针对图片生成过程中出现的领口不符合要求的失败图片，我们提供了专门的重新生成脚本：

### 使用方法

```bash
# 重新生成所有失败图片
python regenerate_failed_images.py

# 批量处理（每次处理10个）
python regenerate_failed_images.py --batch-size 10

# 指定处理范围
python regenerate_failed_images.py --start-index 0 --end-index 100

# 指定失败图片列表文件
python regenerate_failed_images.py --fail-file data/fail.txt
```

### 功能特点

- **智能解析**：自动解析 `fail.txt` 中的失败图片路径
- **增强Prompt**：针对领口问题生成强化的描述文本
- **批量处理**：支持分批处理，避免API频率限制
- **任务追踪**：生成独立的任务文件，便于状态追踪
- **文件命名**：重新生成的图片添加 `_regenerated` 后缀
- **重试机制**：内置重试逻辑，提高成功率

### 领口要求强化

重新生成时特别强调：
- ✅ 必须是圆领、立领或高领设计
- ❌ 严禁V领、低领、衽领（交领）
- ✅ 领口必须完全遮盖脖子
- ✅ 中式服装必须有高领内衬
- ✅ 领口紧贴脖子，不露出任何脖子部位

## 🔄 替换Regenerated图片

当重新生成的图片完成后，可以使用替换脚本将所有regenerated图片替换为原始图片：

### 使用方法

```bash
# 试运行模式（查看将要替换的文件，不实际修改）
python replace_regenerated_images.py

# 实际执行替换
python replace_regenerated_images.py --execute
```

### 功能特点

- **智能识别**：自动扫描done_tasks目录中的所有regenerated任务
- **安全备份**：替换前自动备份原始图片（添加.backup后缀）
- **批量替换**：一次性处理所有regenerated图片
- **详细统计**：显示处理进度和结果统计
- **试运行模式**：默认试运行，确认无误后再执行

### 清理工具

替换完成后，可以使用清理脚本删除不需要的文件：

```bash
# 查看可清理的文件（试运行）
python cleanup_regenerated_files.py --regenerated  # 查看regenerated文件
python cleanup_regenerated_files.py --backup      # 查看备份文件
python cleanup_regenerated_files.py --all         # 查看所有文件

# 实际删除文件
python cleanup_regenerated_files.py --regenerated --execute  # 删除regenerated文件
python cleanup_regenerated_files.py --backup --execute      # 删除备份文件
python cleanup_regenerated_files.py --all --execute         # 删除所有文件
```

### 完整工作流程

1. **识别失败图片**：`python regenerate_failed_images.py`
2. **查询任务状态**：`python check_async_tasks.py`
3. **替换原始图片**：`python replace_regenerated_images.py --execute`
4. **清理临时文件**：`python cleanup_regenerated_files.py --regenerated --execute`

## 📋 项目特色

### ✨ 核心功能
- 🤖 **AI解说文案生成**: 基于豆包大模型的智能文案创作
- 🎨 **双模式图片生成**: 同步模式（实时）+ 异步模式（批量）
- 🎵 **高质量语音合成**: 火山引擎TTS，支持时间戳
- 🎬 **智能视频合成**: 音频、图片、字幕完美同步
- 👥 **角色图片系统**: 五层属性分类，智能角色匹配
- 🚀 **L4 GPU加速**: 专门优化的NVENC编码配置

### 🚀 技术亮点
- ⚡ **异步处理**: 支持大批量任务的异步处理
- 🎯 **智能断句**: 基于语义的字幕优化
- 📁 **模块化设计**: 清晰的代码结构和职责分离
- 🛡️ **内容安全**: 自动规避敏感内容
- 🔧 **配置灵活**: 丰富的自定义配置选项
- 🚀 **GPU优化**: 自动检测并优化L4 GPU性能

## 📝 更新日志

### v3.0.0 (最新)
- 🔄 **双模式图片生成**: 新增同步/异步两种模式
- 📁 **目录结构优化**: Character_Images移至根目录
- 👥 **角色图片系统**: 完整的五层属性分类系统
- ⚡ **性能优化**: 异步处理和资源复用
- 🎯 **智能字幕**: 改进的断句和显示算法

### v2.0.0
- ✨ 智能断句功能
- 🎨 字幕样式优化
- 🛡️ 内容规避机制

### v1.0.0
- 🎉 初始版本发布
- 🤖 基础AI功能

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**