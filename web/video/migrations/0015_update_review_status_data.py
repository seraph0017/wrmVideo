# Generated manually to migrate review_status data from 'pending' to 'not_submitted'

from django.db import migrations


def update_review_status(apps, schema_editor):
    """
    将所有 'pending' 状态的章节更新为 'not_submitted'
    这是因为我们重新定义了审核状态：
    - pending (旧) -> not_submitted (新) - 未审核
    - 新增: reviewing - 审核中
    """
    Chapter = apps.get_model('video', 'Chapter')
    updated_count = Chapter.objects.filter(review_status='pending').update(review_status='not_submitted')
    print(f"已更新 {updated_count} 个章节的审核状态: pending -> not_submitted")


def reverse_update(apps, schema_editor):
    """
    回滚操作：将 'not_submitted' 改回 'pending'
    """
    Chapter = apps.get_model('video', 'Chapter')
    updated_count = Chapter.objects.filter(review_status='not_submitted').update(review_status='pending')
    print(f"已回滚 {updated_count} 个章节的审核状态: not_submitted -> pending")


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0014_alter_chapter_review_status'),
    ]

    operations = [
        migrations.RunPython(update_review_status, reverse_update),
    ]
