# Preston

[![CI](https://github.com/Celeo/preston/workflows/CI/badge.svg?branch=master)](https://github.com/Celeo/preston/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/Celeo/preston/branch/master/graph/badge.svg?token=2R9RY3P229)](https://codecov.io/gh/Celeo/preston)
[![Python version](https://img.shields.io/badge/Python-3.6+-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Preston is a Python library for accessing EVE Online's ESI API.

## Quick links

* EVE ESI: <https://esi.tech.ccp.is/>
* EVE developers: <https://developers.eveonline.com/>

## Installation

From [pip](https://pip.pypa.io/en/stable/):

```sh
pip install preston
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

Additionally, a `post_op` method exists, that takes a dictionary (instead of **kwargs) and another parameter; the former is used like above, to satisfy the URL parameters, and the latter is sent to the ESI endpoint as the payloadd.

For #2, there are 2 methods that you'll need, `get_authorize_url` and `authenticate`, and several `__init__` kwargs.

```python
preston = Preston(
    user_agent='some_user_agent',
    client_id='something',
    client_secret='something',
    callback_url='something',
    scope='maybe_something',
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

### Resuming authentication

If your app uses scopes, it'll receive a `refresh_token` alongside the `access_token`. The access token, per usual, only lasts 20 minutes before it expires. In this situation,
the refresh token can be used to get a *new* access token. If your Preston instance has a refresh token, this will be done automatically when the access token expires.

You can also get this refresh token from the Preston instance with `token = preston.refresh_token`. This can be then stored somewhere (securely) and used again later by
passing the token to Preston's constructor:

```python
preston = Preston(
    user_agent='some_user_agent',
    client_id='something',
    client_secret='something',
    callback_url='something',
    scope='maybe_something',
    refresh_token='your_token_here'
)
```

Preston will take the refresh token and attempt to get a new access token from it.

On that note, you can also pass the `access_token` to a new Preston instance, but there's less of a use case for that, as either you have an app with scopes, yielding a refresh token,
or an authentication-only app where you only use the access token to verify identity and some basic information before moving on.

## Developing

### Building

### Requirements

* Git
* Poetry
* Python 3.6+

### Steps

```sh
git clone https://github.com/Celeo/preston
cd preston
poetry install
```

### Running tests

| | |
| --- | --- |
| No coverage | `poetry run pytest`
| Coverage printout | `poetry run pytest --cov=preston` |
| Coverage report | `poetry run pytest --cov=preston --cov-report=html` |

## License

Licensed under MIT ([LICENSE](LICENSE)).

## Contributing

PRs are welcome. Please follow PEP8 (I'm lenient on E501) and use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
