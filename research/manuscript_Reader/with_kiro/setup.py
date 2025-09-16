"""Setup script for Telugu OCR system."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
readme_path = Path(__file__).parent / "docs" / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").strip().split("\n")
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith("#")]

setup(
    name="telugu-document-ocr",
    version="1.0.0",
    author="Telugu OCR Team",
    author_email="contact@telugu-ocr.com",
    description="A comprehensive OCR system for extracting text from Telugu documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/telugu-document-ocr",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "gpu": [
            "torch>=1.12.0+cu116",
            "torchvision>=0.13.0+cu116",
        ],
        "all": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
            "torch>=1.12.0+cu116",
            "torchvision>=0.13.0+cu116",
        ],
    },
    entry_points={
        "console_scripts": [
            "telugu-ocr=telugu_ocr.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "telugu_ocr": [
            "config/*.yaml",
            "docs/*.md",
        ],
    },
    keywords=[
        "ocr",
        "telugu",
        "document-processing",
        "text-extraction",
        "image-processing",
        "machine-learning",
        "computer-vision",
        "nlp",
        "indian-languages",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-username/telugu-document-ocr/issues",
        "Source": "https://github.com/your-username/telugu-document-ocr",
        "Documentation": "https://github.com/your-username/telugu-document-ocr/docs",
    },
)