from setuptools import setup, find_packages
from stolos.cli import VERSION


setup(
    name='stolosctl',
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click >= 6.0',
        'PyYAML >= 3.11',
        'tabulate >= 0.7.5',
        'requests >= 2.6.1',
    ],
    extras_require={
        'security': ['requests[security] >= 2.6.1'],
        'compose': ['requests >= 2.6.1, < 2.8', 'docker-compose >= 1.7.0'],
    },
    entry_points='''
    [console_scripts]
    stolos=stolos.cli:cli
    stolosctl=stolos.cli:cli
    ''',
)
