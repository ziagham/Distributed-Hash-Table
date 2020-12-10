#!/usr/bin/env python3

import argparse
import os
import json
import re
import signal
import socket
import socketserver
import threading
from threading import Thread, Lock
from http.server import BaseHTTPRequestHandler, HTTPServer
from baseNode import baseNode
import configurations as configs
from address import nodeAddress, networkAddress
from state import nodeState

node = None

class NodeHttpHandler(BaseHTTPRequestHandler):
    global node

    def log_message(self, format, *args):
        pass

#region RESTFul actions
    def do_PUT(self):
        if node.get_state() == False:
            self.send_whole_response(500, "I have sim-crashed")

        elif self.path.startswith("/storage"):
            content_length = int(self.headers.get('content-length', 0))
            key = self.extract_key_from_path(self.path)
            value = self.rfile.read(content_length)
            result = node.putKeyValue(key, value)
            if result is None or result == False:
                data = { "result": "Could not put data with key ({}) to the network.".format(key) }
                self.send_whole_response(404, data)
            else:
                data = { "result": "Value with key ({}) is stored to the network successfully.".format(key) }
                self.send_whole_response(200, data)

    def do_GET(self):
        if self.path.startswith("/node-info"):
            node_info_json = json.dumps(node.get_node_info(), indent=2)
            self.send_whole_response(200, node_info_json, content_type="application/json")

        elif self.path.startswith("/ping"):
            if node.running() == False:
                self.send_whole_response(404, False)
            # elif node.get_state() == False:
            #     self.send_whole_response(404, False)
            else:
                self.send_whole_response(200, node.ping())

        elif self.path.startswith("/isStable"):
            self.send_whole_response(200, node.is_stable())

        elif node.get_state() == False:
            self.send_whole_response(500, "I have sim-crashed")

        elif self.path.startswith("/storage"):
            key = self.extract_key_from_path(self.path)
            result = node.getKey(key)
            if result is None:
                #data = { "result": "No content with key ({}) could be found.".format(key) }
                self.send_whole_response(404, "No object with key '%s' on this node" % key)
            else:
                #data = { 'Key': str(key), 'value': str(result) }
                #result = result.decode("utf-8")
                self.send_whole_response(200, result,'text/plain')

        elif self.path.startswith("/join"):
            null_data = { "result": None }
            id = self.extract_joinKey_from_path(self.path)

            result = node.findSuccessor(id)

            if result is None:
                self.send_whole_response(404, null_data)
            else:
                self.send_whole_response(200, result.serialize())

        elif self.path.startswith("/findsuccessor"):
            null_data = { "result": None }

            if node.running() == False:
                self.send_whole_response(404, null_data)

            id = self.extract_findsuccessorKey_from_path(self.path)
            result = node.findSuccessor(id)
            if result is None:
                self.send_whole_response(404, null_data)
            else:
                self.send_whole_response(200, result.serialize())

        elif self.path.startswith("/findpredecessor"):
            null_data = { "result": None }
            
            if node.running() == False:
                self.send_whole_response(404, null_data)

            id = self.extract_findpredecessorKey_from_path(self.path)
            result = node.get_predecessor()
            if result is None:
                self.send_whole_response(404, null_data)
            else:
                self.send_whole_response(200, result.serialize())

        elif self.path.startswith("/fingertable"):
            self.send_whole_response(200, node.get_fingertable())

        elif self.path.startswith("/neighbors"):
            self.send_whole_response(200, node.get_neighbors())

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)

    def do_POST(self):
        content_length = int(self.headers.get('content-length', 0))
        if self.path == "/sim-recover":
            node.set_state(nodeState.STABLE)
            self.send_whole_response(200, "")
            
        elif self.path == "/sim-crash":
            node.set_state(nodeState.CRASHED)
            self.send_whole_response(200, "")

        elif node.get_state() == False:
            self.send_whole_response(500, "I have sim-crashed")

        elif self.path.startswith("/notify"):
            value = self.rfile.read(content_length).decode('utf-8')
            node.notify(value)

        elif self.path.startswith("/informPredecessor"):
            value = self.rfile.read(content_length).decode('utf-8')
            node.changeSuccessor(value)

        elif self.path.startswith("/informSuccessor"):
            value = self.rfile.read(content_length).decode('utf-8')
            node.changePredecessor(value)

        elif self.path.startswith("/leave"):
            node.leave()
            self.send_whole_response(200, "")

        elif self.path.startswith("/join"):
            nprime = re.sub(r'^/join\?nprime=([\w:-]+)$', r'\1', self.path)
            node.join(nprime)
            self.send_whole_response(200, "")
#end region

#region methods
    def send_whole_response(self, code, content, content_type="text/plain"):
        if isinstance(content, str):
            content = content.encode("utf-8")
            if not content_type:
                content_type = "text/plain"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
        elif isinstance(content, bytes):
            if not content_type:
                content_type = "application/octet-stream"
        elif isinstance(content, object):
            content = json.dumps(content, indent=2)
            content += "\n"
            content = content.encode("utf-8")
            content_type = "application/json"

        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length',len(content))
        self.end_headers()
        self.wfile.write(content)

    def check_route(self, route):
        if (self.path == node): 
            return False
        if self.path.lower().startswith(route.lower()):
            return True
        return False

    def extract_key_from_path(self, path):
        return re.sub(r'/storage/?(\w+)', r'\1', path)

    def extract_joinKey_from_path(self, path):
        return re.sub(r'/join/?(\w+)', r'\1', path)

    def extract_findsuccessorKey_from_path(self, path):
        result = re.sub(r'/findsuccessor/?(\w+)', r'\1', path)
        return result

    def extract_findpredecessorKey_from_path(self, path):
        return re.sub(r'/findpredecessor/?(\w+)', r'\1', path)

    def extract_info_from_route(self, path, specialPart):
        regEx = r'{0}?(\w+)'.format(specialPart)
        result = re.sub(regEx, r'\1', path)
        return result

#end region

def arg_parser():
    parser = argparse.ArgumentParser(prog="node", description="DHT Node")

    parser.add_argument("-p", "--port", type=int, default = configs.DEFAULT_PORT,
            help="port number to listen on, default %d" % configs.DEFAULT_PORT)

    parser.add_argument("--die-after-seconds", type=float,
            default = configs.DIE_AFTER_SECONDS_DEFAULT,
            help="kill server after so many seconds have elapsed, " +
                "in case we forget or fail to kill it, " +
                "default %d (%d minutes)" % (configs.DIE_AFTER_SECONDS_DEFAULT, configs.DIE_AFTER_SECONDS_DEFAULT/60))

    parser.add_argument("remote", type=str, nargs="*",
            help="addresses (host:port) of a DHT node")

    return parser

class ThreadingHttpServer(socketserver.ThreadingMixIn, HTTPServer):
    pass

def run_server(args):
    global server
    global node

    host = networkAddress().get_host_address()
    print(host)
    server = ThreadingHttpServer(('', args.port), NodeHttpHandler)
    node = baseNode(nodeAddress("{}:{}".format(host, args.port)))
    remoteAddress = args.remote

    def server_main():
        print("Starting server on address {} with identity {}.".format(node.get_address(), node.get_identity()))
        if remoteAddress:
            print("connect to {} to join network.".format(remoteAddress))

        server.serve_forever()
        print("Server has shut down")

    def shutdown_server_on_signal(signum, frame):
        print("We get signal (%s). Asking server to shut down" % signum)
        node.leave()
        node.dispose()
        server.shutdown()

    # Start server in a new thread, because server HTTPServer.serve_forever()
    # and HTTPServer.shutdown() must be called from separate threads
    thread = threading.Thread(target=server_main)
    thread.daemon = True
    thread.start()

    join_thread = threading.Thread(target=node.start, args=(remoteAddress))
    join_thread.daemon = True
    join_thread.start()

    # Shut down on kill (SIGTERM) and Ctrl-C (SIGINT)
    signal.signal(signal.SIGTERM, shutdown_server_on_signal)
    signal.signal(signal.SIGINT, shutdown_server_on_signal)

    # Wait on server thread, until timeout has elapsed
    #
    # Note: The timeout parameter here is also important for catching OS
    # signals, so do not remove it.
    #
    # Having a timeout to check for keeps the waiting thread active enough to
    # check for signals too. Without it, the waiting thread will block so
    # completely that it won't respond to Ctrl-C or SIGTERM. You'll only be
    # able to kill it with kill -9.
    thread.join(args.die_after_seconds)
    if thread.is_alive():
        print("Reached %.3f second timeout. Asking server to shut down" % args.die_after_seconds)
        server.shutdown()

    print("Exited cleanly")

if __name__ == "__main__":

    parser = arg_parser()
    args = parser.parse_args()
    run_server(args)
