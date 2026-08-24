from runtime.endpoints import provider_endpoint
from runtime.providers.base import ModelResult


class FakeProvider:
    id = "openai-compatible"

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []
        self.embedding_requests = []

    async def generate(self, model, messages, tools, emit, context):
        self.requests.append({"model": model, "messages": messages, "tools": tools})
        message = self.responses.pop(0)
        if isinstance(message, Exception):
            raise message
        if message.get("content"):
            await emit(message["content"])
        return ModelResult(message, {"prompt_tokens": 3, "completion_tokens": 2})

    async def embed(self, model, texts):
        self.embedding_requests.append({"model": model, "texts": texts})
        return [[float(index)] for index, _ in enumerate(texts)]


def endpoint(
    provider,
    endpoint_id="openai-compatible",
    models=("qwen-test",),
    priority=100,
    embedding_models=(),
):
    return provider_endpoint(
        provider, models, endpoint_id, priority, embedding_models
    )
