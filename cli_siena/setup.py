import logging
from setuptools import (
    setup,
    find_packages,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except Exception as e:
    long_description = "not provided"
    logger.error(f"couldn't retrieve the long package description. {e}")

setup(
    name='siena',
    version='0.0.1a1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # Include special files needed for init project:
        "": ["*.SIENA", "*.siena", "*.tmp", "*.md"],
    },
    description="SIENA tool.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akalankasakalasooriya/siena_text_annotation_tool",
    author="Akalanka Sakalasooriya",
    author_email="himesha@outlook.com",
    # license="MIT",  # TODO: add license
    classifiers=[
        # "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.7.11",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=[
    ],
    entry_points={'console_scripts': ['siena = siena.siena_cli:run_siena_cli']}
)