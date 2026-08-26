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
        return ModelResult(message, _usage())

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


def _usage():
    return {"input_tokens": 3, "cached_input_tokens": 0, "cache_write_input_tokens": 0, "output_tokens": 2, "reasoning_output_tokens": 0}
