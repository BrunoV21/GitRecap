from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="git-recap",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "PyGithub==2.6.1",
        "azure-devops==7.1.0b4",
        "python-gitlab==5.6.0"
    ],
    author="Bruno V.",
    author_email="bruno.vitorino@tecnico.ulisboa.pt",
    description="A modular Python tool that aggregates and formats user-authored messages from repositories.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
