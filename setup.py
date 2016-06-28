from setuptools import setup
import re


with open('prest/prest.py') as f:
    version = re.search(r'(\d+\.\d+\.\d+)', f.read()).group(1)

setup(
    name='EVEPrest',
    author='Matt Boulanger',
    author_email='celeodor@gmail.com',
    version=version,
    license='MIT',
    description='EVE CREST access tool',
    url='https://github.com/Celeo/Prest',
    platforms='any',
    packages=['prest'],
    keywords=['eve online', 'crest', 'api'],
    install_requires=[
        'requests>=2.10.0'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ]
)
