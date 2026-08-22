from runtime.providers.base import ModelResult


class FakeProvider:
    id = "openai-compatible"

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    async def generate(self, model, messages, tools, emit, context):
        self.requests.append({"model": model, "messages": messages, "tools": tools})
        message = self.responses.pop(0)
        if message.get("content"):
            await emit(message["content"])
        return ModelResult(message, {"prompt_tokens": 3, "completion_tokens": 2})

    async def embed(self, model, texts):
        return [[float(index)] for index, _ in enumerate(texts)]
