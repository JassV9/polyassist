from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def analyze_text(self, prompt: str) -> str:
        """Send text prompt, get text response."""
        pass

    @abstractmethod
    async def analyze_image(self, image: bytes, prompt: str) -> str:
        """Send image + text prompt, get text response (vision models)."""
        pass

    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        pass
