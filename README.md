# Preston

[![CI](https://github.com/Celeo/Preston/actions/workflows/ci.yml/badge.svg)](https://github.com/Celeo/Preston/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/Celeo/preston/branch/master/graph/badge.svg?token=2R9RY3P229)](https://codecov.io/gh/Celeo/preston)
[![Python version](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Preston is a Python library for accessing EVE Online's ESI API.

## Quick links

* EVE ESI: <https://esi.evetech.net>
* EVE developers: <https://developers.eveonline.com>

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

Additionally, a `post_op` method exists, that takes a dictionary (instead of **kwargs) and another parameter; the former is used like above, to satisfy the URL parameters, and the latter is sent to the ESI endpoint as the payload.

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

> [!NOTE]
> `get_authorize_url()` takes an optional argument 'state' that you can use to make sure you get the code back from the right user. 
> If you do not set this then the url includes `?state=default`

When you get their callback, take the code paramter from the URL and pass it to `authenticate`:

```python
auth = preston.authenticate('their_code_here')
```

> [!NOTE]
> The return variable and it's reassignment: this method returns a *new* instance, with the corresponding variables and headers setup for authenticated ESI calls.

Finally for #3, having followed the steps above, you just make calls like previously, but you can do so to the authenticated-only endpoints. Make sure that if you're calling
an endpoint that requires a specific scope, your app on EVE Devs has that scoped added and you've supplied it to the Preston initialization.

### Resuming authentication

If your app uses scopes, it'll receive a `refresh_token` alongside the `access_token`. The access token, per usual, only lasts 20 minutes before it expires. In this situation,
the refresh token can be used to get a *new* access token and a *new* refresh token. If your Preston instance has a refresh token, this will be done automatically when the access token expires.

If you want to store your current refresh token so you can fetch data with authorization later on again, you can do that with preston as following.

To get the current refresh token and keep getting informed when it changes, initialize Preston with a refresh token callback function.
This function should look something like this:

```python
def my_refresh_token_callback(preston: Preston):
    # To figure out which user called the callback, you can use the whoami() function.
    current_user_info = preston.whoami()
    character_id = current_user_info.get("character_id")
    scopes = current_user_info.get("scopes")
    
    # Now you probably want store the refresh token somewhere e.g. your db
    # Or something else persistent. In the simple case all users have the same scopes
    # and you are using a python shelve, you would do something like this:
    python_shelve[character_id] = preston.refresh_token
```

You can pass this function to Preston on initialization:

```python
preston = Preston(
    ...,
    refresh_token_callback=my_refresh_token_callback
)
```

Now every time Preston needs to get new tokens, it will also call your function so you can stay up to date.

If you want to resume authentication, you can use the refresh token on initialization:

```python
preston = Preston(
    ...,
    refresh_token='your_refresh_token_here'
)
```
Or you can get an authorized Preston instance from an unauthorized:

```python
auth = preston.authenticate_from_token('your_refresh_token_here')
```

> [!NOTE]
> You can also pass the `access_token` to a new Preston instance, but there's less of a use case for that, as either you have an app with scopes, yielding a refresh token,
> or an authentication-only app where you only use the access token to verify identity and some basic information before moving on.

## Error Handling

Preston usually retries network-related exceptions up to 4 times with exponential backoff (1, 2, 4, 8, ... seconds), and times out any single request
after 6 seconds. This means that at most any single call can take 39 seconds. You can modify this behaviour with optional arguments:
```python
preston = Preston(
    timeout="timeout_per_request_in_seconds",
    retrues="max_number_of_retries",
)
```

For non network related issues, Preston raises the Exceptions generated by requests immediately. 
You can find all possible errors [here](https://requests.readthedocs.io/en/latest/_modules/requests/exceptions/).

A simple error handling scheme might look something like this:

```python
try:
    authed_preston = preston.authenticate_from_refresh(character.token)
except HTTPError as exp:
    # Some kind of error the user has to deal with e.g. no permissions, token revoked on website
    ...
except ConnectionError as exp:
    # Network issue. If it is a background task probably fine to log and skip, if there is a user tell him network is bad
    ...
    # in both cases The exception contains the full response e.g. you can
    print(exp.response.status_code)
    print(exp.response.text)
    # etc.
```

## Developing

### Building

### Requirements

* Git
* uv
* Python 3.8+

### Steps

```sh
git clone https://github.com/Celeo/preston
cd preston
uv sync
```

### Running tests

| | |
| --- | --- |
| No coverage | `uv run pytest`
| Coverage printout | `uv run pytest --cov=preston` |
| Coverage report | `uv run pytest --cov=preston --cov-report=html` |

## License

Licensed under MIT ([LICENSE](LICENSE)).

## Contributing

PRs are welcome. Please follow PEP8 (I'm lenient on E501) and use [Google-style docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html#example-google).
