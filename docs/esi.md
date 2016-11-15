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

TODO
