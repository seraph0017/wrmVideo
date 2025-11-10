"""
Django管理命令：同步章节到数据库

使用方法：
    # 同步所有小说
    python manage.py sync_chapters
    
    # 同步指定小说
    python manage.py sync_chapters --novel-id 20
    
    # 同步指定数据目录
    python manage.py sync_chapters --data-dir ../data/020
"""

import os
import re
import glob
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from video.models import Novel, Chapter


class Command(BaseCommand):
    help = '同步文件系统中的章节到数据库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--novel-id',
            type=int,
            help='指定要同步的小说ID'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            help='指定要同步的数据目录（如 ../data/020）'
        )
        parser.add_argument(
            '--data-root',
            type=str,
            default='../data',
            help='data根目录路径（默认: ../data）'
        )

    def handle(self, *args, **options):
        """执行同步命令"""
        # 获取项目根目录
        project_root = settings.BASE_DIR.parent
        
        try:
            if options['data_dir']:
                # 同步指定目录
                data_dir = Path(project_root) / options['data_dir']
                novel_id = self.extract_novel_id_from_path(str(data_dir))
                if not novel_id:
                    raise CommandError(f'无法从路径中提取小说ID: {data_dir}')
                
                self.stdout.write(f"同步指定目录: {data_dir}")
                self.stdout.write("=" * 60)
                created, updated, skipped = self.sync_novel_chapters(novel_id, str(data_dir))
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(self.style.SUCCESS("同步完成！统计信息："))
                self.stdout.write(f"  创建章节数: {created}")
                self.stdout.write(f"  更新章节数: {updated}")
                self.stdout.write(f"  跳过章节数: {skipped}")
                self.stdout.write("=" * 60)
                
            elif options['novel_id']:
                # 同步指定小说
                data_root = Path(project_root) / options['data_root']
                data_dir = data_root / f'{options["novel_id"]:03d}'
                if not data_dir.exists():
                    raise CommandError(f'数据目录不存在: {data_dir}')
                
                self.stdout.write(f"同步指定小说: ID={options['novel_id']}")
                self.stdout.write("=" * 60)
                created, updated, skipped = self.sync_novel_chapters(options['novel_id'], str(data_dir))
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(self.style.SUCCESS("同步完成！统计信息："))
                self.stdout.write(f"  创建章节数: {created}")
                self.stdout.write(f"  更新章节数: {updated}")
                self.stdout.write(f"  跳过章节数: {skipped}")
                self.stdout.write("=" * 60)
                
            else:
                # 同步所有小说
                data_root = Path(project_root) / options['data_root']
                self.sync_all_novels(str(data_root))
                
        except Exception as e:
            raise CommandError(f'同步失败: {e}')

    def extract_novel_id_from_path(self, data_dir):
        """从路径中提取小说ID"""
        match = re.search(r'/(\d{3})/?$', str(data_dir))
        if match:
            return int(match.group(1))
        return None

    def parse_narration_file(self, narration_path):
        """解析narration.txt文件，提取章节信息"""
        try:
            with open(narration_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取章节标题
            chapter_dir = os.path.dirname(narration_path)
            chapter_name = os.path.basename(chapter_dir)
            
            # 提取解说内容并计算字数
            narration_contents = re.findall(r'<解说内容>(.*?)</解说内容>', content, re.DOTALL)
            total_words = sum(len(n.strip()) for n in narration_contents)
            
            # 提取章节风格
            format_match = re.search(r'<章节风格>(.*?)</章节风格>', content)
            chapter_format = format_match.group(1).strip() if format_match else '未知'
            
            return {
                'title': chapter_name,
                'word_count': total_words,
                'format': chapter_format
            }
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"解析narration文件失败 {narration_path}: {e}"))
            return None

    def check_video_exists(self, chapter_dir, project_root):
        """检查章节目录下是否存在完整视频文件"""
        video_patterns = [
            os.path.join(chapter_dir, '*_complete.mp4'),
            os.path.join(chapter_dir, 'complete.mp4'),
            os.path.join(chapter_dir, '*.mp4')
        ]
        
        for pattern in video_patterns:
            videos = glob.glob(pattern)
            if videos:
                # 返回相对路径
                rel_path = os.path.relpath(videos[0], project_root)
                return rel_path
        
        return None

    def count_chapter_files(self, chapter_dir):
        """统计章节目录下的文件数量"""
        stats = {
            'script_count': 0,
            'audio_count': 0,
            'subtitle_count': 0,
            'image_count': 0
        }
        
        # 统计脚本文件（narration.txt）
        if os.path.exists(os.path.join(chapter_dir, 'narration.txt')):
            stats['script_count'] = 1
        
        # 统计旁白音频文件（*.mp3）
        audio_files = glob.glob(os.path.join(chapter_dir, '*.mp3'))
        stats['audio_count'] = len(audio_files)
        
        # 统计字幕文件（*.ass）
        subtitle_files = glob.glob(os.path.join(chapter_dir, '*.ass'))
        stats['subtitle_count'] = len(subtitle_files)
        
        # 统计图片文件（*.jpeg, *.jpg, *.png）
        image_patterns = [
            os.path.join(chapter_dir, '*.jpeg'),
            os.path.join(chapter_dir, '*.jpg'),
            os.path.join(chapter_dir, '*.png')
        ]
        image_files = []
        for pattern in image_patterns:
            image_files.extend(glob.glob(pattern))
        stats['image_count'] = len(image_files)
        
        return stats

    def sync_novel_chapters(self, novel_id, data_dir):
        """同步指定小说的所有章节到数据库"""
        project_root = settings.BASE_DIR.parent
        
        # 获取或创建Novel对象
        novel, created = Novel.objects.get_or_create(
            id=novel_id,
            defaults={
                'name': f'小说{novel_id:03d}',
                'word_count': 0,
                'type': '未分类'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ 创建小说记录: ID={novel_id}, 名称={novel.name}"))
        else:
            self.stdout.write(f"✓ 找到小说记录: ID={novel_id}, 名称={novel.name}")
        
        # 查找所有章节目录
        chapter_dirs = sorted(glob.glob(os.path.join(data_dir, 'chapter_*')))
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for chapter_dir in chapter_dirs:
            # 提取章节编号
            chapter_name = os.path.basename(chapter_dir)
            match = re.search(r'chapter_(\d+)', chapter_name)
            if not match:
                self.stdout.write(self.style.WARNING(f"✗ 跳过无效章节目录: {chapter_dir}"))
                skipped_count += 1
                continue
            
            chapter_num = int(match.group(1))
            
            # 查找narration.txt文件
            narration_path = os.path.join(chapter_dir, 'narration.txt')
            if not os.path.exists(narration_path):
                self.stdout.write(self.style.WARNING(f"✗ 跳过（无narration.txt）: {chapter_name}"))
                skipped_count += 1
                continue
            
            # 解析章节信息
            chapter_info = self.parse_narration_file(narration_path)
            if not chapter_info:
                self.stdout.write(self.style.WARNING(f"✗ 跳过（解析失败）: {chapter_name}"))
                skipped_count += 1
                continue
            
            # 检查视频文件
            video_path = self.check_video_exists(chapter_dir, project_root)
            
            # 统计章节文件数量
            file_stats = self.count_chapter_files(chapter_dir)
            
            # 创建或更新Chapter记录
            chapter, created = Chapter.objects.update_or_create(
                novel=novel,
                title=chapter_info['title'],
                defaults={
                    'word_count': chapter_info['word_count'],
                    'format': chapter_info['format'],
                    'video_path': video_path,
                    'script_count': file_stats['script_count'],
                    'audio_count': file_stats['audio_count'],
                    'subtitle_count': file_stats['subtitle_count'],
                    'image_count': file_stats['image_count']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ 创建章节: {chapter_info['title']} "
                    f"(字数: {chapter_info['word_count']}, "
                    f"脚本: {file_stats['script_count']}, "
                    f"旁白: {file_stats['audio_count']}, "
                    f"字幕: {file_stats['subtitle_count']}, "
                    f"图片: {file_stats['image_count']}, "
                    f"视频: {'有' if video_path else '无'})"
                ))
                created_count += 1
            else:
                self.stdout.write(
                    f"  ✓ 更新章节: {chapter_info['title']} "
                    f"(字数: {chapter_info['word_count']}, "
                    f"脚本: {file_stats['script_count']}, "
                    f"旁白: {file_stats['audio_count']}, "
                    f"字幕: {file_stats['subtitle_count']}, "
                    f"图片: {file_stats['image_count']}, "
                    f"视频: {'有' if video_path else '无'})"
                )
                updated_count += 1
        
        # 更新小说的总字数
        total_words = sum(c.word_count for c in novel.chapters.all())
        novel.word_count = total_words
        novel.save()
        self.stdout.write(self.style.SUCCESS(f"✓ 更新小说总字数: {total_words}"))
        
        return created_count, updated_count, skipped_count

    def sync_all_novels(self, data_root):
        """同步data目录下所有小说的章节到数据库"""
        self.stdout.write(f"开始扫描目录: {data_root}")
        self.stdout.write("=" * 60)
        
        # 查找所有小说目录
        novel_dirs = sorted(glob.glob(os.path.join(data_root, '[0-9][0-9][0-9]')))
        
        if not novel_dirs:
            self.stdout.write(self.style.WARNING("✗ 未找到任何小说目录"))
            return None
        
        self.stdout.write(f"找到 {len(novel_dirs)} 个小说目录\n")
        
        total_stats = {
            'novels': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0
        }
        
        for novel_dir in novel_dirs:
            novel_id = self.extract_novel_id_from_path(novel_dir)
            if not novel_id:
                self.stdout.write(self.style.WARNING(f"✗ 跳过无效目录: {novel_dir}"))
                continue
            
            self.stdout.write(f"\n处理小说 ID={novel_id:03d} ({novel_dir})")
            self.stdout.write("-" * 60)
            
            created, updated, skipped = self.sync_novel_chapters(novel_id, novel_dir)
            
            total_stats['novels'] += 1
            total_stats['created'] += created
            total_stats['updated'] += updated
            total_stats['skipped'] += skipped
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("同步完成！统计信息："))
        self.stdout.write(f"  处理小说数: {total_stats['novels']}")
        self.stdout.write(f"  创建章节数: {total_stats['created']}")
        self.stdout.write(f"  更新章节数: {total_stats['updated']}")
        self.stdout.write(f"  跳过章节数: {total_stats['skipped']}")
        self.stdout.write("=" * 60)
        
        return total_stats

