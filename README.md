# Polysistia: AI Coaching Assistant for The Battle of Polytopia

Polysistia is a real-time AI coaching overlay for the turn-based strategy game The Battle of Polytopia (Steam/Windows).

## Features

- **Screen Capture:** High-performance capture using `dxcam` with `mss` fallback.
- **Computer Vision:** Isometric grid mapping, tile classification, unit detection, and health bar reading using OpenCV.
- **OCR:** UI text extraction (turn number, stars, income, score) using Tesseract.
- **Knowledge Base:** Comprehensive data on technologies, units, buildings, and tribes.
- **Stateful Tracking:** Persistent game state across turns, including fog-of-war memory.
- **LLM Integration:** Provider-agnostic interface for OpenAI, Anthropic, and Ollama.
- **Transparent Overlay:** PyQt6-based HUD for real-time feedback.

## Setup

1. **Prerequisites:**
   - Python 3.11+
   - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and added to PATH.
   - The Battle of Polytopia (Steam/Windows version).

2. **Installation:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configuration:**
   - Rename `calibration_template.json` to `calibration.json` and adjust as needed (or use the calibration wizard).
   - Set environment variables for LLM API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.

## Usage

- **Start Polysistia:**
  ```bash
  polysistia
  ```
- **Calibration Wizard:**
  ```bash
  python tools/calibration_wizard.py
  ```
- **F1 Toggle:** Use F1 to toggle the overlay visibility while in-game.

## Architecture Overview

Polysistia follows a pipeline architecture:
`Capture -> Change Detection -> Vision Pipeline (OCR + CV) -> State Tracking -> Overlay Rendering`

- `polysistia/capture`: Handles screen grabbing.
- `polysistia/vision`: Extract raw game state from images.
- `polysistia/state`: Manages persistent game state and models.
- `polysistia/knowledge`: Encodes Polytopia rules and data.
- `polysistia/llm`: Interfaces with language models.
- `polysistia/overlay`: Minimal PyQt6 HUD.
