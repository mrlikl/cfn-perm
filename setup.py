from setuptools import setup, find_packages

setup(
    name="cfn-perm",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "boto3",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "cfn-perm=source.app:main",
        ],
    },
    author="S Murali Krishnan",
    author_email="mrlikrsh@gmail.com",
    description="A tool to automatically generate IAM permissions from CloudFormation templates",
    keywords="aws, cloudformation, iam, permissions",
    url="https://github.com/mrlikl/cfn-perm.git",
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
