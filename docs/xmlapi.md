# XMLAPI

## Attributes and calls

Unlike CREST, the endpoints are manually constructed and are in the form of `scope/endpoint.xml.aspx`. For example, to get a list of active alliances and their members, the endpoint is `AllianceList` under the `eve` scope: `eve/AllianceList.xml.aspx`.

For Preston, building the path to the endpoint is done by calling attributes on the root object and what it returns:

```python
preston.eve.AllianceList
```

Calling the built object fetches the data from the API (or from the local cache):

```python
data = preston.eve.AllianceList()
```

## Additional parameters

For most endpoints, additional data needs to be passed as part of the request in the form of GET parameters.

Passing key-value pairs to the endpoint is done by passing them to the call:

```python
data = preston.eve.CharacterAffiliation(ids=91316135)
```

## Using the cache

Page are cached when requested and are returned from the cache when subsequently requested inside the expiration time of the page. This caching does not extend beyond the `preston.xmlapi.Preston` object - if you use a new instance, it will not have a populated cache.

## Authentication

To reduce the amount of typing, `preston.xmlapi.Preston` can store an authentication keyID and vCode and automatically pass them to called endpoints:

```python
preston = Preston(key=1, code='')
data = preston.account.APIKeyInfo()
```

## Returned data

Preston takes the XML from the endpoint and turns it into a dictionary using [xmltodict](https://github.com/martinblech/xmltodict). Therefore, navigating through the result is like navigating through a dictionary:

```python
>>> data = preston.eve.CharacterAffiliation(ids=91316135)
>>> data
OrderedDict([('rowset', OrderedDict([('@name', 'characters'), ('@key', 'characterID'), ('@columns', 'characterID,characterName,corporationID,corporationName,allianceID,allianceName,factionID,factionName'), ('row', OrderedDict([('@characterID', '91316135'), ('@characterName', 'Celeo Servasse'), ('@corporationID', '98134538'), ('@corporationName', 'Wormbro'), ('@allianceID', '99006650'), ('@allianceName', 'The Society For Unethical Treatment Of Sleepers'), ('@factionID', '0'), ('@factionName', '')]))]))])
>>> data['rowset']['row']['@corporationName']
'Wormbro'
```

## User Agent

To set the User-Agent header, pass it to the `preston.xmlapi.Preston` constructor:

```python
preston = Preston(user_agent='')
```
