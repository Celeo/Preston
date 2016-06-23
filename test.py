#!/usr/bin/env python
import time

from prest import Prest


# prest = Prest()
# prest = Prest(logging_level=20) # info
prest = Prest(logging_level=10) # debug

# print(prest.serverName)
start = time.time()
print(prest.wars().pageCount)
print(time.time() - start, 'seconds')
start = time.time()
print(prest.wars().pageCount)
print(time.time() - start, 'seconds')
start = time.time()
print(prest.wars().pageCount)
print(time.time() - start, 'seconds')


print(prest.marketTypes().pageCount)

# print(prest.opportunities.tasks().items.find(name='Jump Through a Wormhole').description)
# print(prest.systems().items.find(name='Jita')().planets[4].moons[4]().name)
