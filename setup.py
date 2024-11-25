from setuptools import setup, find_packages

setup(
    name="py-helm-gen",
    version="1.0",
    description="A Python package to generate Helm charts from Docker Compose files",
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


