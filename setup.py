from setuptools import setup
import re


with open('preston/__init__.py') as f:
    version = re.search(r'(\d+\.\d+\.\d+)', f.read()).group(1)

setup(
    name='Preston',
    author='Matt Boulanger',
    author_email='celeodor@gmail.com',
    version=version,
    license='MIT',
    description='EVE CREST and XMLAPI access tool',
    url='https://github.com/Celeo/Preston',
    platforms='any',
    packages=['preston', 'preston.crest', 'preston.xmlapi', 'preston.esi'],
    keywords=['eve online', 'crest', 'api'],
    install_requires=[
        'requests>=2.10.0',
        'xmltodict>=0.10.2'
    ],
    classifiers=[
        'Environment :: Console',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ]
)
