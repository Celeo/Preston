#!/usr/bin/env python
from prest import Prest, CRESTException


try:
    prest = Prest()
    print(prest.motd.eve())
except CRESTException as e:
    print(e)
