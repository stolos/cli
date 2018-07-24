from setuptools import setup, find_packages
from stolos import VERSION


setup(
    name="stolosctl",
    version=VERSION,
    author="SourceLair PC",
    url="https://www.sourcelair.com/",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click >= 6.0",
        "PyYAML >= 3.11",
        "tabulate >= 0.7.5",
        "requests >= 2.11.0",
        "six",
    ],
    extras_require={
        "security": ["requests[security] >= 2.11.0"],
        "compose": ["docker-compose >= 1.7.0"],
    },
    entry_points="""
    [console_scripts]
    stolos=stolos.cli:cli
    stolosctl=stolos.cli:cli
    """,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
)
