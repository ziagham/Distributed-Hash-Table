#!/usr/bin/env python3

import socket
from hashing import consistent_hashing

class nodeAddress:
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

class networkAddress:
	def get_host_address(self):
		host_name = socket.gethostname()
		name = host_name.split('.', 1)
		if (len(name)>1):
			host_name = host_name.split('.', 1)[0]
		else:
			host_name = self.get_ip_address(host_name)
		return host_name

	def get_ip_address(self, host_name):
		ip_address = socket.gethostbyname(host_name)
		return ip_address

	def __str__(self):
		return "{}".format(self.get_host_address)
