from setuptools import setup, find_packages

setup(
    name="job-assistant-models",
    version="0.1.0",
    packages=find_packages(),
    description="Shared data models for job assistant applications",
    author="Your Name",
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
)