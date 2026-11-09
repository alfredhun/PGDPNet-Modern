#!/usr/bin/env python
# Modernized PGDPNet setup.py: Pure Python with native torchvision.ops
import os
from setuptools import find_packages, setup

requirements = [
    "torch>=2.0.0",
    "torchvision>=0.15.0",
    "yacs",
    "matplotlib",
    "tqdm",
    "opencv-python",
    "scikit-image",
    "pandas",
    "imagehash",
    "sympy",
    "scipy",
]

setup(
    name="geo_parse",
    version="0.2.0",
    author="Ming-Liang Zhang (Modernized)",
    description="Geometric diagram analysis in modern PyTorch",
    packages=find_packages(exclude=("configs", "tests")),
    install_requires=requirements,
    include_package_data=True,
    zip_safe=False,
)
