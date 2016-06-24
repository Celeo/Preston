# Prest

## Summary

Prest is a Python library for accessing EVE Online's CREST API.

## Installation

From [pip](https://pip.pypa.io/en/stable/):

```bash
pip install git+https://git.celeodor.com/Celeo/Prest.git
```

## Use

### Initialization

```python
from prest import Prest

prest = Prest()
```

### Attributes and calls

Accessing an attribute from the `prest.Prest` instance will navigate through the API. Calling an attribute will load that resource. Calling a `prest.Prest` instance will re-cache the root URI, but this is done automatically when the class is first initialized with `prest = Prest()`.

So, if you wanted to access the X position of the Kimoto constellation, the call would be:

```python
prest.constellations().items.find(name='Kimotoro')().position.x
```

There's no need to re-call the base `prest.Prest` here as it's cached when the class is initialized.

From the [base url](https://crest-tq.eveonline.com/) "constellations" is a root-level dictionary item with a "href" item, which can be called to navigate to [that page](https://crest-tq.eveonline.com/constellations/).

From there, the `.items` attribute dives into the `items` dictionary key and then a `find` method is used to get an element from the list of dictionaries (you could loop through the items yourself, but `find` is for convenience). This dictionary has a "href" element, so call the attribute to navigate [there](https://crest-tq.eveonline.com/constellations/20000020/).

Now on the final page, access the "position" key and finally its "x" key, which is `-134996400468185440`.

### Examples

1. Market types -> page count

```python
prest.marketTypes().pageCount
```

2. "Jump Through a Wormhole" opportunity

```python
prest.opportunities.tasks().items.find(name='Jump Through a Wormhole').description
```

3. Jita 4-4 moon name

```python
prest.systems().items.find(name='Jita')().planets[3].moons[3]().name
```

### Authentication

Accessing the authenticated parts of CREST is done through authenticating Prest:

```python
from prest import *

prest = Prest(client_id='', client_secret='', client_callback='')
prest.get_authorize_url()
auth = prest.authenticate(code)
```

In the code above, `get_authorize_url` returns a URL to redirect a web app client to so they can log into EVE's SSO. Once they've redirected back to your web application, pass the code in the returning URL from EVE to the `authenticate` call and assign the resulting `prest.AuthPrest` object.

This `prest.AuthPrest` object works the same as the unathenticated `prest.Prest` object: use attributes and calls to navigate and load the CREST, respectively.

Example of accessing a character's location:

```python
print(auth.decode().character().location())
```
