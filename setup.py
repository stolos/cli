from setuptools import setup, find_packages


setup(
    name='stolosctl',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'clint',
        'pyyaml',
        'tabulate',
        'requests==2.10.0',
    ],
    entry_points='''
    [console_scripts]
    stolos=stolos.cli:cli
    stolosctl=stolos.cli:cli
    ''',
)
