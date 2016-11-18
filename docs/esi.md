# ESI

## Attributes and calls

Calling a `preston.esi.preston.Page` object will fetch the build URL and return the data from that page. If the page's contents are cached, the cached data will be returned without making another request to the website.

Getting an attribute by text from the base `preston.esi.preston.Preston` object will start a URL building in the form of the returned `preston.esi.preston.Page` object. Calling an attribute on one of these `Page` objects will continue building the URL. In the event where you are rqeuired to append a numerical value to the URL, like in the case of supplying an alliance id for the endpoint to fetch an alliance's members, you can do so with the stanard `dict.__getitem__` notation.

## Using the cache

Page are cached when requested and are returned from the cache when subsequently requested inside the expiration time of the page. This caching does not extend beyond the object on which the request was made - if you use a new instance, it will not have a populated cache. The design is to keep the same `preston.esi.preston.Preston` object around and build URLs off of it.

## Examples

Getting the list of alliances

```python
preston.alliances()
```

Get the coporation members of an alliance:

```python
preston.alliances[99006650].corporations()
```

List all public structures:

```python
preston.universe.structures()
```

## Authentication

Accessing the authenticated parts of ESI is done through authenticating Preston:

```python
from preston.esi import Preston

preston = Preston(client_id='', client_secret='', client_callback='')
preston.get_authorize_url()
auth = preston.authenticate(code)
```

In the code above, `get_authorize_url` returns a URL to redirect a web app client to so they can log into EVE's SSO. Once they've redirected back to your web application, pass the code in the returning URL from EVE to the `authenticate` call and assign the resulting `preston.AuthPreston` object.

This `preston.AuthPreston` object works the same as the unathenticated `preston.esi.Preston` object: use attributes and calls to navigate and load ESI data, respectively.

Example of accessing a character's location:

```python
print(auth.decode().character().location())
```

## Refresh tokens

When you authenticate for accessing ESI using a scope, Preston will get two tokens back: the access token, which is a temporary (20 minutes) token used for accessing ESI, and a refresh token that doesn't expire but cannot be used to directly access ESI. When the access token expires, Preston will get another access token from ESI using the refresh token.

Since the refresh token doesn't expire, you'll want to keep that somewhere safe. Preston doesn't handle this for you.

To start an authenticated session with Preston using a previously-fetched refresh token (you can get the existing refresh token with `preston.AuthPreston.refresh_token` as a `str`), do the following:

```python
preston = Preston(client_id='', client_secret='', client_callback='', user_agent='')
auth = preston.use_refresh_token('previous-refresh-token')
```

## User Agent

To set the User-Agent header, pass it to the `preston.esi.Preston` constructor:

```python
preston = Preston(user_agent='')
```
