from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).resolve().parent
README = (BASE_DIR / "README.md").read_text(encoding="utf-8")

setup(
    name="aa-captrack",
    version="1.0.9b4.1",
    description="Capital ship movement early warning plugin for AllianceAuth",
    long_description=README,
    long_description_content_type="text/markdown",
    author="SteveTh3Piirate",
    license="MIT",
    url="https://github.com/SteveTh3Piirate/aa-captrack",
    project_urls={
        "Source": "https://github.com/SteveTh3Piirate/aa-captrack",
        "Issues": "https://github.com/SteveTh3Piirate/aa-captrack/issues",
    },
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[
        "allianceauth>4.0,<5.0.0a5",
        "allianceauth-corptools>=2.15.2,<=3.0.0b8",
        "requests>=2.0",
    ],
    classifiers=[
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
