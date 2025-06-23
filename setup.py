#!/usr/bin/env python

from setuptools import setup, find_packages


version = '0.1'

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='smartCoW',
    version=version,
    author='Mateusz Kielan',
    author_email='mateuszkielan38@gmail.com',
    url='https://github.com/MateuszKielan/BachelorThesis_CoW_Interface/',
    description='Smart and Intuitive UI for CoW',
    long_description = open('README.md').read(),
    long_description_content_type="text/markdown",
    license='GLP3',
    include_package_data=True,
    zip_safe=True,
    keywords=['rdf', 'linked data', 'csv', 'GUI', 'converter'],
    python_requires='>=3.8',
    packages=find_packages(where='Interface'),
    package_dir={'': 'Interface'},
    install_requires=[
        'kivy',
        'kivymd',
        'requests',
        'pandas',
        'numpy',
        'SPARQLWrapper',
        'cow-csvw',
        'PyYAML==6.0'
    ],
    entry_points={'console_scripts': ['scow = main:main']},
)

