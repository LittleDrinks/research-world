"""Research-facing copy at the user and agent write boundary."""
import re

TOY_WORDS = re.compile(r'演示|实例|示例|(?<![a-z])(?:demo|toy)(?![a-z])', re.IGNORECASE)
DISPLAY_FIELDS = ('title', 'text', 'summary', 'note')


def validate_node_language(content):
    for field in DISPLAY_FIELDS:
        value = content.get(field)
        if isinstance(value, str) and TOY_WORDS.search(value):
            raise ValueError(f'content.{field}: 请直接描述研究问题、方法或结果，去掉占位词')
    return content
