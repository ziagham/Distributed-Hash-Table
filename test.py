#!/usr/bin/env python3

import sys
import os
import random
import time
import threading
import subprocess
import http.client
import configurations as configs
from hashing import consistent_hashing
import json
import re
from address import networkAddress

class Response(object): pass

class Request(object):
	def _describe_exception(self, e):
		return "%s: %s" % (type(e).__name__, e)

	def _search_header_tuple(self, headers, header_name):
		header_name = header_name.lower()

		for key, value in headers:
			if key.lower() == header_name:
				return value
		return None

	def _determine_charset(self, content_type):
		cmatch = re.match("text/plain; ?charset=(\\S*)", content_type)
		if cmatch:
			return cmatch.group(1)
		else:
			return "latin_1"

	def send_request(self, host_port, method, url, body=None, accept_statuses=[200]):
		def describe_request():
			return "%s %s%s" % (method, host_port, url)

		conn = None
		try:
			conn = http.client.HTTPConnection(host_port)
			try:
				conn.request(method, url, body)
				r = conn.getresponse()
			except Exception as e:
				raise Exception(describe_request()
						+ " --- "
						+ self._describe_exception(e))

			status = r.status
			if status not in accept_statuses:
				raise Exception(describe_request() + " --- unexpected status %d" % (r.status))

			headers = r.getheaders()
			body = r.read()

		finally:
			if conn:
				conn.close()

		content_type = self._search_header_tuple(headers, "Content-type")

		if content_type == "application/json":
			try:
				body = json.loads(body)
			except Exception as e:
				raise Exception(describe_request()
						+ " --- "
						+ self._describe_exception(e)
						+ " --- Body start: "
						+ body[:30])

		if content_type != None and content_type.startswith("text/plain") \
				and sys.version_info[0] >= 3:
			charset = self._determine_charset(content_type)
			body = body.decode(charset)

		r2 = Response()
		r2.status = status
		r2.headers = headers
		r2.body = body

		return r2

class TestNodes:
	def __init__(self):
		self._threads = {}
		self.generated_keys = {}
		self.default_port = configs.START_PORT_FROM
		self.unstable_nodes = {}
		self.host_address = networkAddress().get_host_address()

	def generate_key(self, default):
		port = configs.START_PORT_FROM if default == 0 else (random.randrange(configs.START_PORT_FROM + 1, configs.PORT_NUMBER_RANGE))
		address = "{}:{}".format(self.host_address, port)
		key = consistent_hashing(address)

		if (key in self.generated_keys.keys()):
			key, port = self.generate_key(default)

		return key, port

	def generate_ports(self, default):
		key, port = self.generate_key(default)
		self.generated_keys[key] = port
		return port 

	def start_stand_alone(self):
		i = 0
		while i < configs.DHT_SIZE:
			port = self.generate_ports(default = 0 if i == 0 else 1)
			self._threads[i] = threading.Thread(target=self._run_stand_alone, args=[port])
			print("Port number: {} - counter {}".format(port, i))
			i = i  + 1

		for key in self._threads:
			self._threads[key].start()

	def start_joining(self):
		for key in self.generated_keys:
			port= self.generated_keys[key]
			if port == configs.START_PORT_FROM:
				continue
			
			nodeA = "{}:{}".format(self.host_address, port)
			nodeB = "{}:{}".format(self.host_address, configs.START_PORT_FROM)
			r = Request()
			r.send_request(nodeA, "POST", "/join?nprime="+nodeB)

	def stop(self):
		for key in self._threads:
			self._threads[key].join()

	def get_python_name(self):
		py = "python3"
		if os.name == 'nt':
			py = "python"
		return py

	def _run_stand_alone(self, port):
		subprocess.call([self.get_python_name(), 'storageNode.py', "-p {}".format(port)])

	def run(self, port, node=None):
		if node is None:
			subprocess.call([self.get_python_name(), 'storageNode.py', "-p {}".format(port)])
		else:
			subprocess.call([self.get_python_name(), 'storageNode.py', "-p {}".format(port), node])

	def check_join_statbility(self):
		running = True
		self.unstable_nodes = self.generated_keys.copy()
		r = Request()
		start_time = time.time()
		while running:
			for key in self.generated_keys:
				port= self.generated_keys[key]
				nodeA = "{}:{}".format(self.host_address, port)
				result = r.send_request(nodeA, "GET", "/isStable") 
				if result.body == True:
					if key in self.unstable_nodes: del self.unstable_nodes[key]

			if len(self.unstable_nodes)<=0:
				running = False
				continue

		end_time = time.time()
		total = end_time - start_time
		print()
		print("Total time to become stable: ", total)
		print()

	def check_leave_statbility(self):
		keys = random.sample(list(self.generated_keys), 1 if configs.DHT_SIZE==1 else int(configs.DHT_SIZE/2))
		left_keys = { k : self.generated_keys[k] for k in set(self.generated_keys) - set(keys) }
		running = True
		r = Request()
		print(left_keys)
		start_time = time.time()

		for key in keys:
			port= self.generated_keys[key]
			nodeA = "{}:{}".format(self.host_address, port)
			result = r.send_request(nodeA, "POST", "/leave") 

		self.unstable_nodes = left_keys.copy()

		time.sleep(2)

		while running:
			for key in left_keys:
				port= self.generated_keys[key]
				nodeA = "{}:{}".format(self.host_address, port)
				result = r.send_request(nodeA, "GET", "/isStable") 
				if result.body == True:
					if key in self.unstable_nodes: del self.unstable_nodes[key]

			if len(self.unstable_nodes)<=0:
				running = False
				continue

		end_time = time.time()
		total = end_time - start_time
		print()
		print("Total time to become stable: ", total)
		print()

if __name__ == "__main__":
	nodes = TestNodes()
	nodes.start_stand_alone()
	time.sleep(30.0)
	nodes.start_joining()
	# nodes.check_join_statbility()
	# nodes.check_leave_statbility()
	nodes.stop()
	# exit()

	
