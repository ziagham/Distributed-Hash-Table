#!/usr/bin/env python3

import hashlib
from address import nodeAddress
from hashing import consistent_hashing

class finger:
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
