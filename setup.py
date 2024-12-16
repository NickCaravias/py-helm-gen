from setuptools import setup, find_packages

# read the contents of README file for description
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pyhelmgen",
    version="1.3",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Nick Caravias",
    author_email="nick.caravias@gmail.com",
    license="MIT",
    packages=find_packages(where="src"),  # Look inside `src/` for the packages
    package_dir={"": "src"},  # The package directory is `src`
    install_requires=[
        "pyyaml>=5.4.0", 
    ],
    extras_require={
        "dev": [
            "pytest>=6.2",
            "black>=21.6b0",
            "flake8>=3.9"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)


