"""Setup script for pyblink."""

from setuptools import setup, find_packages

setup(
    name="pyblink",
    version="0.1.0",
    packages=find_packages(exclude=["tests", "tests.*", "backend", "frontend"]),
    python_requires=">=3.11",
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "hypothesis>=6.0",
        ],
    },
)