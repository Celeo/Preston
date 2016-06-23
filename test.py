#!/usr/bin/env python
from prest import Prest


prest = Prest()

print(prest)

print(prest.serverName)
print(prest.wars)
print(prest.wars().pageCount)
