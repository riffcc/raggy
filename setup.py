from setuptools import setup, find_packages

setup(
    name="iroh-example",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "iroh==0.27.0",
    ],
    extras_require={
        "test": ["pytest", "pytest-asyncio"],
    },
)
