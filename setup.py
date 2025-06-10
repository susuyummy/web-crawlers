from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="susuyummy-web-crawlers",
    version="0.1.0",
    description="A collection of web crawlers for various websites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="susuyummy",
    author_email="cscs878787@gmail.com",
    url="https://github.com/susuyummy/web-crawlers",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "pandas>=2.1.0",
        "openpyxl>=3.1.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    project_urls={
        "Bug Reports": "https://github.com/susuyummy/web-crawlers/issues",
        "Source": "https://github.com/susuyummy/web-crawlers",
    },
) 