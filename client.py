#!/usr/bin/env python3

import argparse
import http.client
import json
import random
import uuid
import time

total_get_seconds = 0
total_put_seconds = 0

def arg_parser():
    parser = argparse.ArgumentParser(prog="client", description="DHT client")

    parser.add_argument("nodes", type=str, nargs="+",
            help="addresses (host:port) of nodes to test")

    return parser

def generate_pairs(count):
    pairs = {}
    for x in range(0, count):
        key = str(uuid.uuid4())
        value = str(uuid.uuid4())
        pairs[key] = value
    return pairs

def put_value(node, key, value):
    conn = http.client.HTTPConnection(node)
    conn.request("PUT", "/storage/"+key, value)
    conn.getresponse()
    conn.close()

def get_value(node, key):
    global total_get_seconds
    get_start_time = time.time()
    conn = http.client.HTTPConnection(node)
    conn.request("GET", "/storage/"+key)
    resp = conn.getresponse()
    headers = resp.getheaders()
    if resp.status != 200:
        value = None
    else:
        value = resp.read()
    contenttype = "text/plain"
    for h, hv in headers:
        if h=="Content-type":
            contenttype = hv
    if contenttype == "text/plain":
        value = value.decode("utf-8")
    conn.close()
    get_end_time = time.time() - get_start_time
    total_get_seconds += get_end_time
    return value

def get_neighbours(node):
    conn = http.client.HTTPConnection(node)
    conn.request("GET", "/neighbors")
    resp = conn.getresponse()
    if resp.status != 200:
        neighbors = []
    else:
        body = resp.read()
        neighbors = json.loads(body)
    conn.close()
    return neighbors

def walk_neighbours(start_nodes):
    to_visit = start_nodes
    visited = set()
    while to_visit:
        next_node = to_visit.pop()
        visited.add(next_node)
        neighbors = get_neighbours(next_node)
        for neighbor in neighbors:
            if neighbor not in visited:
                to_visit.append(neighbor)
    return visited

def simple_check(nodes):
    print("Simple put/get check, retreiving from same node ...")

    tries = 20
    pairs = generate_pairs(tries)

    successes = 0
    node_index = 0
    start = time.time()
    for key, value in pairs.items():
        try:
            put_value(nodes[node_index], key, value)
            returned = get_value(nodes[node_index], key)

            if returned == value:
                successes+=1
        except:
            pass

        node_index = (node_index+1) % len(nodes)

    request_time = time.time() - start

    success_percent = float(successes) / float(tries) * 100
    print("Stored and retrieved %d pairs of %d (%.1f%%) with (%.1f)" % (
            successes, tries, success_percent, tries/request_time ))


def retrieve_from_different_nodes(nodes):
    print("Retrieving from different nodes ...")

    tries = 20
    pairs = generate_pairs(tries)
    successes = 0
    start = time.time()
    for key, value in pairs.items():
        try:
            put_value(random.choice(nodes), key, value)
            returned = get_value(random.choice(nodes), key)

            if returned == value:
                successes+=1
        except:
            pass

    request_time = time.time() - start

    success_percent = float(successes) / float(tries) * 100
    print("Stored and retrieved %d pairs of %d (%.1f%%) with (%.1f%%)" % (
            successes, tries, success_percent, tries/request_time ))


def get_nonexistent_key(nodes):
    print("Retrieving a nonexistent key ...")

    key = str(uuid.uuid4())
    node = random.choice(nodes)
    print("%s -- GET /%s" % (node, key))
    try:
        conn = http.client.HTTPConnection(node)
        conn.request("GET", "/storage/"+key)
        resp = conn.getresponse()
        value = resp.read().strip()
        conn.close()
        print("Status: %s (expected 404)" % resp.status)
        print("Data  : %s" % value)
    except Exception as e:
        print("GET failed with exception:")
        print(e)

def main(args):

    nodes = set(args.nodes)
    nodes |= walk_neighbours(args.nodes)
    nodes = list(nodes)
    print("%d nodes registered: %s" % (len(nodes), ", ".join(nodes)))

    if len(nodes)==0:
        raise RuntimeError("No nodes registered to connect to")

    print()
    simple_check(nodes)

    print()
    retrieve_from_different_nodes(nodes)

    print()
    get_nonexistent_key(nodes)

if __name__ == "__main__":

    parser = arg_parser()
    args = parser.parse_args()
    main(args)
