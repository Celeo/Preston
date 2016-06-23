# Design

## Initialization

```python
from prest import Prest

prest = Prest()
```

## Attributes and calls

Accessing an attribute from the `prest.Prest` instance will navigate through the API. Calling an attribute will load that resource. Calling a `prest.Prest` instance will re-cache the root URI, but this is done automatically when the class is first initialized with `prest = Prest()`.

So, if you wanted to access the X position of the Kimoto constellation, the call would be:

```python
prest.constellations().items.find(name='Kimotoro')().position.x
```

There's no need to re-call the base `prest.Prest` here as it's cached when the class is initialized.

From the [base url](https://crest-tq.eveonline.com/) "constellations" is a root-level dictionary item with a "href" item, which can be called to navigate to [that page](https://crest-tq.eveonline.com/constellations/).

From there, the `.items` attribute dives into the `items` dictionary key and then a `find` method is used to get an element from the list of dictionaries (you could loop through the items yourself, but `find` is for convenience). This dictionary has a "href" element, so call the attribute to navigate [there](https://crest-tq.eveonline.com/constellations/20000020/).

Now on the final page, access the "position" key and finally its "x" key, which is `-134996400468185440`.

## Examples

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
prest.systems().items.find(name='Jita')().planets[4].moons[4]().name
```
