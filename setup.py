#!/usr/bin/env python

from setuptools import setup


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
    packages = ['scow'],
    package_dir = {'scow': 'Interface'},
    entry_points={'console_scripts' : [ 'scow = scow.main:main' ]},
    install_requires=[
        "cython<3",
        "pyyaml",
        "kivy[base]",
        "kivymd==2.0.1",
        "pandas",
        "numpy",
        "SPARQLWrapper<2.0",
        "cow-csvw"
        ]
)

