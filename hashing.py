#!/usr/bin/env python3

#description "INF3200: Distributed Systems Fundamentals Mandatory Assignment 1"
#authors    [
#               {"Name": "Amin Ziagham Ahwazi", "Email":"azi011@uit.no"}, 
#               {"Name": "Keerthana Sivakumar", "Email":"ksi055@uit.no"}
#           ]

from hashlib import sha1
from configurations import *

def hash_to_hex(strInput):
    x = sha1(str(strInput).encode())
    return x.hexdigest()

def hex_to_int(strInput):
    result = hash_to_hex(strInput)
    x = int(result,16)
    return x

def consistent_hashing(strInput):
    x= hex_to_int(strInput) % (DHT_SIZE)
    return x