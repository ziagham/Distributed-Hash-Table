#!/usr/bin/env python3

import configurations as configs

# Helper function to determine if a key falls within a range
def inrange(c, a, b):
	a = a % (configs.DHT_SIZE)
	b = b % (configs.DHT_SIZE)
	c = c % (configs.DHT_SIZE)
	if a < b:
		return a <= c and c < b
	return a < c or c <= b
