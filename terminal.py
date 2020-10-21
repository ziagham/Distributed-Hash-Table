#!/usr/bin/env python3

#description "INF3200: Distributed Systems Fundamentals Mandatory Assignment 1"
#authors    [
#               {"Name": "Amin Ziagham Ahwazi", "Email":"azi011@uit.no"}, 
#               {"Name": "Keerthana Sivakumar", "Email":"ksi055@uit.no"}
#           ]

import argparse
import http.client
import json
import random
import uuid
from hashing import hash_to_hex

remoteAddress = ""

def arg_parser():
    parser = argparse.ArgumentParser(prog="client", description="DHT client")

    parser.add_argument("remoteAddress", type=str, nargs="+",
            help="address (host:port) of a node to connect")

    return parser

def put_value(node, key, value):
    conn = http.client.HTTPConnection(node)
    conn.request("PUT", "/storage/"+key, value)
    resp = conn.getresponse()
    value = resp.read()
    value = value.decode("utf-8")
    conn.close()
    return value

def get_value(node, key):
    conn = http.client.HTTPConnection(node)
    conn.request("GET", "/storage/"+key)
    resp = conn.getresponse()
    value = resp.read()
    value = value.decode("utf-8")
    conn.close()
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

def __operationMenu():
    print("-----------------------------------")
    print("Executive and monitoring operations")
    print("-----------------------------------")
    print("Enter [1] to [Search]")
    print("Enter [2] to [Insert key/value]")
    print("Enter [3] to [Display Neighbours]")
    print("Enter [4] to [Exit]")

def _displayMenu():
    while True:
        __operationMenu()
        choice  = input("Enter your choice :")
        if  choice == '1':
            key = input("Enter key:")
            result = get_value(remoteAddress[0], key)
            print()
            print("LookUp Key")
            print("----------")
            print(result)
            print()

        if choice == '2':
            key = input("Enter key:")
            value = input("Enter value:")
            result = put_value(remoteAddress[0], key, value)
            print()
            print("Put Value")
            print("---------")
            print(result)
            print()

        if choice == '3':
            result = get_neighbours(remoteAddress[0])
            print()
            print("Neighbors")
            print("---------")
            print(result)
            print()
        if choice == '4':
            exit(0)

def main(args):
    global remoteAddress
    remoteAddress = args.remoteAddress
    _displayMenu()

if __name__ == "__main__":

    parser = arg_parser()
    args = parser.parse_args()
    main(args)