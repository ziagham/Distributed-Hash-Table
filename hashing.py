#!/usr/bin/env python3

from hashlib import md5
import configurations as configs

def hash_to_hex(strInput):
    x = md5(str(strInput).encode())
    return x.hexdigest()

def hex_to_int(strInput):
    result = hash_to_hex(strInput)
    x = int(result,16)
    return x

def consistent_hashing(strInput):
    x= hex_to_int(strInput) % (configs.DHT_SIZE)
    return x
