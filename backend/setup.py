import os
from setuptools import setup, find_packages


def read_requirements():
    """Read requirements.txt if it exists, otherwise return empty list"""
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r") as f:
            requirements = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return requirements


setup(
    name="backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=read_requirements(),
    # ... other setup args
)
