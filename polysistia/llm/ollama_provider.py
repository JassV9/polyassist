import httpx
from .base import LLMProvider

import json

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def analyze_text(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False}
            )
            data = response.json()
            return data["response"]

    async def analyze_image(self, image: bytes, prompt: str) -> str:
        # Note: Not all Ollama models support vision. This assumes a model like 'llava'.
        import base64
        base64_image = base64.b64encode(image).decode('utf-8')

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "images": [base64_image],
                    "stream": False
                }
            )
            data = response.json()
            return data["response"]

    @property
    def supports_vision(self) -> bool:
        # This could be model-dependent.
        return "llava" in self.model
