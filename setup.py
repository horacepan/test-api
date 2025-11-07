#!/usr/bin/env python3
"""
Setup script for Kamino Liquidity Analysis Tool
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kamino-liquidity-analysis",
    version="1.0.0",
    author="Kamino Analysis Team",
    description="A tool to assess liquidity risk for Kamino's Main Market",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/kamino-liquidity-analysis",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "kamino-analyze=kamino_liquidity_analysis.main:main",
        ],
    },
    include_package_data=True,
)
