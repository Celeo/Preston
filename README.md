# Preston

[![Build Status](https://travis-ci.org/Celeo/Preston.svg?branch=master)](https://travis-ci.org/Celeo/Preston)
[![codecov](https://codecov.io/gh/Celeo/Preston/branch/master/graph/badge.svg)](https://codecov.io/gh/Celeo/Preston)

Preston is a Python library for accessing EVE Online's ESI API.

## Quick links

* EVE ESI: https://esi.tech.ccp.is/
* EVE third-party documentation: http://eveonline-third-party-documentation.readthedocs.io
* EVE developers: https://developers.eveonline.com/

## Installation

From [pip](https://pip.pypa.io/en/stable/):

```bash
pip install preston
```

From GitHub:

```bash
git clone https://github.com/Celeo/Preston.git
cd Preston
python setup.py install
```

## Initialization

```python
from preston import Preston

preston = Preston()
```

There are values that you can pass to `__init__` as kwargs; those are detailed in the docstring for the class.

## Usage

There are 3 main things that Preston does:

1. Unauthenticated calls to ESI
2. User authentication
3. Authenticated calls to ESI for that user

For #1, all you need to do is initialize a Preston object and make the call:

```python
preston = Preston(
    user_agent='some_user_agent'
)

data = preston.get_op('get_characters_character_id', character_id=91316135)
# ...
```

You should always include a good `user_agent`.

For #2, there are 2 methods that you'll need, `get_authorize_url` and `authenticate`, and several `__init__` kwargs.

```python
preston = Preston(
    user_agent='some_user_agent',
    client_id='something',
    client_secret='something',
    callback_url='something',
    scope='maybe something',
)
```

You can find the last 4 values in your application on the [EVE Dev site](https://developers.eveonline.com/).

When you have a Preston instance constructed like this, you can make the call to `get_authorize_url`:

```python
preston.get_authorize_url()
# https://login.eveonline.com/oauth/...
```

This is the URL that your user needs to visit and complete the flow. They'll be redirected to your app's callback URL, so you have to be monitoring that.

When you get their callback, take the code paramter from the URL and pass it to `authenticate`:

```python
auth = preston.authenticate('their_code_here')
```

Note the return variable and it's reassignment: this method returns a *new* instance, with the corresponding variables and headers setup for authenticated ESI calls.

Finally for #3, having followed the steps above, you just make calls like previously, but you can do so to the authenticated-only endpoints. Make sure that if you're calling
an endpoint that requires a specific scope, your app on EVE Devs has that scoped added and you've supplied it to the Preston initialization.


## Contributing

PRs are welcome. Please follow PEP8 (I'm lenient on E501) and use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
