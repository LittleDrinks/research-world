import base64
import json

MAX_BYTES = 4 * 1024 * 1024


async def read_text(events):
    chunks, size, exit_code = [], 0, None
    async for line in events:
        event = json.loads(line)
        if event.get('error'):
            raise ValueError('工作区文件读取失败')
        if 'data' in event:
            chunk = base64.b64decode(event['data'], validate=True)
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError('Artifact 超过 4 MiB')
            chunks.append(chunk)
        exit_code = event.get('exitCode', exit_code)
    if exit_code != 0:
        raise ValueError('文件读取未成功完成；请检查路径、文件大小与 UTF-8 编码')
    return b''.join(chunks).decode('utf-8')
