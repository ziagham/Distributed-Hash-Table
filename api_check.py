#!/usr/bin/env python3

import argparse
import json
import re
import random
import threading
import string
import time
import unittest
import uuid

# Logger
import logging
logging.basicConfig()
logger = logging.getLogger()

# Python version check
import sys

if sys.version_info[0] <= 2:
    import httplib
    import urlparse

elif sys.version_info[0] >= 3:
    import http.client as httplib

else:
    logger.warn("Unexpected Python version", sys.version_info())

# Global variables set from options and used in unit tests
# (since it's hard to parameterize tests in Python 2)

SETTLE_MS_DEFAULT = 20
settle_ms = SETTLE_MS_DEFAULT

test_nodes = []

def set_test_nodes(nodes):
    global test_nodes
    test_nodes = nodes

def parse_args():
    parser = argparse.ArgumentParser(prog="api_check", description="node API checker")

    parser.add_argument("--settle-ms", type=int,
            default=SETTLE_MS_DEFAULT,
            help="After a join/leave call, wait for the network to settle (default {} ms)"
                .format(SETTLE_MS_DEFAULT))

    parser.add_argument("nodes", type=str, nargs="*",
            help="addresses (host:port) of nodes to test")

    return parser.parse_args()

def describe_exception(e):
    return "%s: %s" % (type(e).__name__, e)

class Response(object): pass

def search_header_tuple(headers, header_name):
    header_name = header_name.lower()

    for key, value in headers:
        if key.lower() == header_name:
            return value
    return None

def determine_charset(content_type):
    cmatch = re.match("text/plain; ?charset=(\\S*)", content_type)
    if cmatch:
        return cmatch.group(1)
    else:
        return "latin_1"

def do_request(host_port, method, url, body=None, accept_statuses=[200]):
    def describe_request():
        return "%s %s%s" % (method, host_port, url)

    conn = None
    try:
        conn = httplib.HTTPConnection(host_port)
        try:
            conn.request(method, url, body)
            r = conn.getresponse()
        except Exception as e:
            raise Exception(describe_request()
                    + " --- "
                    + describe_exception(e))

        status = r.status
        if status not in accept_statuses:
            raise Exception(describe_request() + " --- unexpected status %d" % (r.status))

        headers = r.getheaders()
        body = r.read()

    finally:
        if conn:
            conn.close()

    content_type = search_header_tuple(headers, "Content-type")

    if content_type == "application/json":
        try:
            body = json.loads(body)
        except Exception as e:
            raise Exception(describe_request()
                    + " --- "
                    + describe_exception(e)
                    + " --- Body start: "
                    + body[:30])

    if content_type != None and content_type.startswith("text/plain") \
            and sys.version_info[0] >= 3:
        charset = determine_charset(content_type)
        body = body.decode(charset)

    r2 = Response()
    r2.status = status
    r2.headers = headers
    r2.body = body

    return r2

class MetaTest(unittest.TestCase):

    def test_determine_charset(self):
        self.assertEqual(determine_charset("text/plain; charset=utf-8"), "utf-8")
        "hello utf-8".encode("utf-8").decode("utf-8")

        self.assertEqual(determine_charset("text/plain; charset=latin1"), "latin1")
        "hello latin1".encode("latin1").decode("latin1")

        self.assertEqual(determine_charset("text/plain"), "latin_1")
        "hello latin_1".encode("latin_1").decode("latin_1")

class SimpleApiCheck(unittest.TestCase):

    def setUp(self):
        if len(test_nodes) < 1:
            raise unittest.SkipTest("Need at least one node")

        self.node = test_nodes[0]

    def test_get_nonexistent_value_404(self):
        key = "api-test-key-nonexistent-key-{}".format(uuid.uuid4())
        r = do_request(self.node, "GET", "/storage/"+key, accept_statuses=[404])

    def test_kv_put_and_get(self):
        key = "api-test-key-{}".format(uuid.uuid4())
        value = "api-test-value-{}".format(uuid.uuid4())

        r = do_request(self.node, "PUT", "/storage/"+key, value)
        r = do_request(self.node, "GET", "/storage/"+key)

        self.assertEqual(r.body, value)

    def test_node_info_json(self):
        r = do_request(self.node, "GET", "/node-info")

        content_type = search_header_tuple(r.headers, "Content-type")
        self.assertEqual(content_type, "application/json",
                    "Headers should specify Content-Type: application/json")

        self.assertIn("node_key", r.body)
        self.assertIn("successor", r.body)
        self.assertIn("others", r.body)
        self.assertIn("sim_crash", r.body)

        if sys.version_info[0] <= 2:
            json_str_type = unicode
        if sys.version_info[0] >= 3:
            json_str_type = str

        if not isinstance(r.body["node_key"], int):
            self.assertIsInstance(r.body["node_key"], json_str_type)

        self.assertIsInstance(r.body["successor"], json_str_type)
        self.assertIsInstance(r.body["others"], list)
        self.assertIsInstance(r.body["sim_crash"], bool)

class JoinLeaveApiCheck(unittest.TestCase):

    def setUp(self):
        if len(test_nodes) < 2:
            raise unittest.SkipTest("Need at least two nodes")

        self.nodeA = test_nodes[0]
        self.nodeB = test_nodes[1]

    def test_join_leave(self):
        # Make node A is not part of the network
        r = do_request(self.nodeA, "POST", "/leave")
        time.sleep(settle_ms / 1000.0)

        r = do_request(self.nodeA, "GET", "/node-info")
        # In a single-node network, the node should be its own successor
        self.assertEqual(r.body["successor"], self.nodeA)

        # Join one node to the other
        r = do_request(self.nodeA, "POST", "/join?nprime="+self.nodeB)
        time.sleep(settle_ms / 1000.0)

        r = do_request(self.nodeA, "GET", "/node-info")
        # In a two-node network, each should be their own successor
        # Here, we just check the first one, so that the dummy node can pass
        self.assertEqual(r.body["successor"], self.nodeB)

class SimCrashApiCheck(unittest.TestCase):

    def setUp(self):
        if len(test_nodes) < 1:
            raise unittest.SkipTest("Need at least one node")

        self.nodeA = test_nodes[0]

    def test_sim_crash_recover(self):
        # Make sure node A is not part of the network
        r = do_request(self.nodeA, "POST", "/leave")
        time.sleep(settle_ms / 1000.0)

        # --------------------------------------------------
        # Make sure node A is not crashed
        r = do_request(self.nodeA, "POST", "/sim-recover")
        time.sleep(settle_ms / 1000.0)

        r = do_request(self.nodeA, "GET", "/node-info")
        # Node state should be not crashed
        self.assertEqual(r.body["sim_crash"], False)

        # Node should respond to requests
        r = do_request(self.nodeA, "POST", "/leave")
        time.sleep(settle_ms / 1000.0)

        # --------------------------------------------------
        # Simulate crash
        r = do_request(self.nodeA, "POST", "/sim-crash")
        time.sleep(settle_ms / 1000.0)

        # Crashed node should not respond to requests
        self.assertRaises(Exception, lambda: do_request(self.nodeA, "POST", "/leave"))
        time.sleep(settle_ms / 1000.0)

        # Crashed node should still respond with info
        r = do_request(self.nodeA, "GET", "/node-info")
        # Node state should be crashed
        self.assertEqual(r.body["sim_crash"], True)

        # --------------------------------------------------
        # Simulate recovery
        r = do_request(self.nodeA, "POST", "/sim-recover")
        time.sleep(settle_ms / 1000.0)

        # Node should respond to requests
        r = do_request(self.nodeA, "POST", "/leave")
        time.sleep(settle_ms / 1000.0)

        r = do_request(self.nodeA, "GET", "/node-info")
        # Node state should be no-longer crashed
        self.assertEqual(r.body["sim_crash"], False)

if __name__ == "__main__":

    args = parse_args()

    test_nodes = args.nodes
    settle_ms = args.settle_ms

    test_suite = unittest.TestSuite()
    test_loader = unittest.TestLoader()

    test_suite.addTests(test_loader.loadTestsFromTestCase(MetaTest))
    test_suite.addTests(test_loader.loadTestsFromTestCase(SimpleApiCheck))
    test_suite.addTests(test_loader.loadTestsFromTestCase(JoinLeaveApiCheck))
    test_suite.addTests(test_loader.loadTestsFromTestCase(SimCrashApiCheck))

    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)
