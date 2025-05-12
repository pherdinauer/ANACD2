from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("json_downloader/requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="anac-json-downloader",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Utility per il download di file JSON dal portale ANAC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/anac-json-downloader",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "anac-downloader=json_downloader.main:main",
        ],
    },
    include_package_data=True,
) 