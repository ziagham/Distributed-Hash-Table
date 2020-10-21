#!/usr/bin/env python3

#description "INF3200: Distributed Systems Fundamentals Mandatory Assignment 1"
#authors    [
#               {"Name": "Amin Ziagham Ahwazi", "Email":"azi011@uit.no"}, 
#               {"Name": "Keerthana Sivakumar", "Email":"ksi055@uit.no"}
#           ]

import address
import hashlib
from hashing import *

class finger(object):
    def __init__(self, address):
        self._identity = consistent_hashing(address)
        self._address = address

    def this(self):
        result = self
        return result

    def serialize(self):
        result = {"identity":self._identity, "address":str(self._address)}
        return result

    def get_identity(self):
        return self._identity

    def get_address(self):
        return self._address