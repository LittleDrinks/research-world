"""One document projection for reading and export."""
import yaml


def render_document(record):
    properties = {k: v for k, v in record.content.items() if k not in {'text', 'origin', 'attachments'}}
    properties.update(id=record.id, type=record.type, revision=record.revision,
                      status=record.content.get('status', 'open'), tags=[label['name'] for label in record.labels])
    return '---\n' + yaml.safe_dump(properties, allow_unicode=True, sort_keys=False) + '---\n\n' + record.content.get('text', '')
