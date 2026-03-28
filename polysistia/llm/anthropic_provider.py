from anthropic import AsyncAnthropic
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20240620"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def analyze_text(self, prompt: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def analyze_image(self, image: bytes, prompt: str) -> str:
        import base64
        base64_image = base64.b64encode(image).decode('utf-8')

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
        )
        return response.content[0].text

    @property
    def supports_vision(self) -> bool:
        return True
