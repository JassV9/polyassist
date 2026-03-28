from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

import json
import os

class Region(BaseModel):
    x: int
    y: int
    w: int
    h: int

class TileGrid(BaseModel):
    origin: tuple[int, int]
    dx: int = 64
    dy: int = 56
    rows: int = 11
    cols: int = 11

class Calibration(BaseModel):
    window_title: str = "The Battle of Polytopia"
    tesseract_cmd: str = "C:/Program Files/Tesseract-OCR/tesseract.exe"
    regions: dict[str, list[int]]
    tile_grid: TileGrid
    resolution: tuple[int, int] = (1920, 1080)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POLYSISTIA_", env_file=".env")

    calibration_path: str = "calibration.json"
    template_path: str = "calibration_template.json"

    # LLM Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # Vision Settings
    change_threshold: float = 0.05
    poll_rate: float = 1.0

    # Logging
    log_level: str = "INFO"

    def load_calibration(self) -> Calibration:
        path = self.calibration_path if os.path.exists(self.calibration_path) else self.template_path
        with open(path, "r") as f:
            data = json.load(f)
            return Calibration(**data)

settings = Settings()
