"""Research-facing copy at the user and agent write boundary."""
import re

TOY_WORDS = re.compile(r'演示|实例|示例|(?<![a-z])(?:demo|toy|sgi)(?![a-z])', re.IGNORECASE)
DISPLAY_FIELDS = ('title', 'text', 'summary', 'note')


def validate_node_language(content):
    fields = {field: content.get(field) for field in DISPLAY_FIELDS}
    attachments = content.get('attachments', [])
    if isinstance(attachments, list):
        fields.update({f'attachments.{i}.name': item.get('name') for i, item in enumerate(attachments) if isinstance(item, dict)})
    for field, value in fields.items():
        if isinstance(value, str) and TOY_WORDS.search(value):
            raise ValueError(f'content.{field}: 请直接描述研究问题、方法或结果，去掉占位词及数据集指代')
    return content
