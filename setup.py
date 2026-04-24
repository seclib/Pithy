"""
PIThy - Setup for pip install
Permet l'installation de la commande 'pithy' globalement.
"""

from setuptools import setup, find_packages

setup(
    name="pithy",
    version="0.3.0",
    description="PIThy — Mini OS IA Local",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "requests",
        "chromadb",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "pithy=cli:main",
        ],
    },
)
