# Preston

## Summary

Preston is a Python library for accessing EVE Online's CREST API.

## Installation

From [pip](https://pip.pypa.io/en/stable/):

```bash
pip install preston
```

## Initialization

```python
from preston.crest import Preston
# or
from preston.xmlapi import Preston


preston = Preston()
```

## CREST

### Attributes and calls

* Calling
  * on `preston.Preston`: reload the base URL data
    * `preston()` -> the same `preston.Preston`
  * on `preston.APIElement`: navigate to a new page
    * `preston.foo()` -> `preston.APIElement`
* Getting attribute by text or item by index
  * from `preston.Preston`: return a data subset or navigate to a new page
    * `preston.foo` -> `str`, `int`, `float`, `preston.APIElement` of data subset, `preston.APIElement` to new page
  * from `preston.APIElement`: return a data subset
    * `preston.foo.bar` -> `str`, `int`, `float`, `preston.APIElement`

To reduce typing, `preston.Preston.__getattr__` combines the functionality of `preston.APIElement.__getattr__` and `preston.APIElement.__call__` so that calls can be made like `preston.foo` instead of `preston().foo`.

If you wanted to access the X position of the Kimoto constellation, the call would be:

```python
preston.constellations().items.find(name='Kimotoro')().position.x
```

From the [base url](https://crest-tq.eveonline.com/) "constellations" is a root-level dictionary item with a "href" item, which can be called to navigate to [that page](https://crest-tq.eveonline.com/constellations/).

From there, the `.items` attribute dives into the `items` dictionary key and then a `find` method is used to get an element from the list of dictionaries (you could loop through the items yourself, but `find` is for convenience). This dictionary has a "href" element, so call the attribute to navigate [there](https://crest-tq.eveonline.com/constellations/20000020/).

Now on the final page, access the "position" key and finally its "x" key, which is `-134996400468185440`.

### Examples

1. Market types -> page count

```python
preston.marketTypes().pageCount
```

2. "Jump Through a Wormhole" opportunity description

```python
preston.opportunities.tasks().items.find(name='Jump Through a Wormhole').description
```

3. Jita 4-4 moon name

```python
preston.systems().items.find(name='Jita')().planets[3].moons[3]().name
```

### Using the cache

When you make a call to `preston.foo`, the root CREST URL data stored locally will be checked for an expired cache timer (the root URL's data is loaded when instantiating a new `preston.Preston` object, you don't need to do it manually). If it's expired, the root URL will be gotten anew and cached. This is similar for `preston.foo().bar().baz()` - if all of `foo`, `bar`, and `baz` were dictionaries with `'href'` keys that pointed to new pages, each would use the cache to retrieve the page, only making a new request to CREST if the local copy of the page is either non-existent or expired.

However, when getting attributes from a page, like `preston.foo().bar.baz`, neither `bar` or `baz` on the page will be using the cache. Thus, in order to make the same call multiple times over a period of time and using the cache, either make the full `preston.foo().bar.baz` call again, or save the last-called element as a local variable and call that:

```python
foo = preston.foo

print(foo().bar.baz)

# later:
print(foo().bar.baz)

# later:
print(foo().bar.baz)
```

### Authentication

Accessing the authenticated parts of CREST is done through authenticating Preston:

```python
from preston import *

preston = Preston(client_id='', client_secret='', client_callback='')
preston.get_authorize_url()
auth = preston.authenticate(code)
```

In the code above, `get_authorize_url` returns a URL to redirect a web app client to so they can log into EVE's SSO. Once they've redirected back to your web application, pass the code in the returning URL from EVE to the `authenticate` call and assign the resulting `preston.AuthPreston` object.

This `preston.AuthPreston` object works the same as the unathenticated `preston.Preston` object: use attributes and calls to navigate and load CREST data, respectively.

Example of accessing a character's location:

```python
print(auth.decode().character().location())
```

#### Refresh tokens

When you authenticate for accessing CREST using a scope, Preston will get two tokens back: the access token, which is a temporary (20 minutes) token used for accessing CREST, and a refresh token that doesn't expire but cannot be used to directly access CREST. When the access token expires, Preston will get another access token from CREST using the refresh token.

Since the refresh token doesn't expire, you'll want to keep that somewhere safe. Preston doesn't handle this for you.

To start an authenticated session with Preston using a previously-fetched refresh token (you can get the existing refresh token with `preston.AuthPreston.refresh_token` as a `str`), do the following:

```python
preston = Preston(client_id='', client_secret='', client_callback='')
auth = preston.use_refresh_token('previous-refresh-token')
```

## XMLAPI

TODO
