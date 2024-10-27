from setuptools import setup, find_packages

setup(
    name="raggy",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.29.0",
        "iroh==0.27.0",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "huggingface-hub>=0.19.4",
        "tokenizers>=0.15.0",
        "pillow>=10.1.0",
        "httpx>=0.25.2",
    ],
)
