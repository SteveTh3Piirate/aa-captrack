from setuptools import setup, find_packages

setup(
    name="aa-captrack",
    version="0.1.2",
    description="Capital ship movement early warning plugin for AllianceAuth",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "allianceauth-corptools==2.15.2",
        "requests",
    ],
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
    ],
)