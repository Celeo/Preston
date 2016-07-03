#!/bin/sh
pandoc --from=markdown --to=rst --output=README.rst README.md || exit 1
python setup.py sdist upload -r pypi || exit 1
rm README.rst || exit 1
echo 'Done'
