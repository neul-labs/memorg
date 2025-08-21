from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("pyproject.toml", "r", encoding="utf-8") as fh:
    # Parse version from pyproject.toml
    import re
    content = fh.read()
    version_match = re.search(r'version = "([^"]+)"', content)
    version = version_match.group(1) if version_match else "0.1.0"

setup(
    name="memorg",
    version=version,
    author="Dipankar Sarkar",
    author_email="me@dipankar.name",
    description="A hierarchical context management system for Large Language Models that acts as an external memory layer, helping LLMs maintain context over extended interactions while managing token usage efficiently.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/skelf-research/memorg",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=[
        "openai>=1.79.0",
        "rich>=14.0.0",
        "tiktoken>=0.9.0",
        "aiosqlite>=0.21.0",
        "numpy>=2.2.6",
        "usearch>=2.17.7",
        "python-dotenv>=1.1.0",
        "fastmcp>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "memorg=app.cli_entry:main",
        ],
    },
)