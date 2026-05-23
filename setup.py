from setuptools import setup

setup(
    name="computeid-cli",
    version="1.0.0",
    description="CLI tool for ComputeID — cryptographic identity for AI compute infrastructure",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="ComputeID",
    author_email="hello@compute-id.com",
    url="https://github.com/trustedaicompute-ops/computeid-sdk",
    py_modules=["cli"],
    install_requires=[
        "click>=8.0.0",
        "requests>=2.28.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "computeid=cli:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Security :: Cryptography",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="gpu identity certificates quantum-safe ai agents security cli computeid",
)
