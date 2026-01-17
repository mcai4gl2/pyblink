"""Setup script for pyblink."""

from setuptools import find_packages, setup

setup(
    name="pyblink",
    version="0.1.0",
    description="Blink protocol implementation in Python",
    packages=find_packages(),
    python_requires=">=3.11",
)