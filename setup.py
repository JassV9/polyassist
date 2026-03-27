from setuptools import setup, find_packages

setup(
    name="polysistia",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dxcam>=0.4.0",
        "mss>=9.0.1",
        "opencv-python>=4.8.0",
        "pytesseract>=0.3.10",
        "Pillow>=10.0.0",
        "pywin32>=306",
        "numpy>=1.24.0",
        "PyQt6>=6.5.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "openai>=1.0.0",
        "anthropic>=0.30.0",
        "httpx>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            "polysistia=polysistia.main:main",
        ],
    },
    python_requires=">=3.11",
)
