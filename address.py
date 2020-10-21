#!/usr/bin/env python3

#description "INF3200: Distributed Systems Fundamentals Mandatory Assignment 1"
#authors    [
#               {"Name": "Amin Ziagham Ahwazi", "Email":"azi011@uit.no"}, 
#               {"Name": "Keerthana Sivakumar", "Email":"ksi055@uit.no"}
#           ]

from hashing import *

# Helper function to determine if a key falls within a range
def inrange(c, a, b):
	a = a % (DHT_SIZE)
	b = b % (DHT_SIZE)
	c = c % (DHT_SIZE)
	if a < b:
		return a <= c and c < b
	return a < c or c <= b

class Address:
	def __init__(self,*args):
		self._address = args[0]

	def __hash__(self):
		return consistent_hashing(self._address) 

	def __cmp__(self, other):
		return other.__hash__() < self.__hash__()

	def __eq__(self, other):
		return other.__hash__() == self.__hash__()

	def __str__(self):
		return "{}".format(self._address)