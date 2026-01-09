from setuptools import setup, find_packages

setup(
    name="aa-captrack",
    version="0.1.0",
    description="Capital ship movement early warning plugin for AllianceAuth",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "allianceauth-corptools>=4.0.0",
    ],
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
    ],
)