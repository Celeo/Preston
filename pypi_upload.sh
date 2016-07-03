#!/bin/sh
pandoc --from=markdown --to=rst --output=README.rst README.md
python setup.py sdist upload -r pypi
rm README.rst
echo 'Done'
