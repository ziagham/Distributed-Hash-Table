#!/usr/bin/env python3

import sys
import http.client
import json
import time
import threading
import os
from utility import *
from finger import finger
from hashing import hash_to_hex, consistent_hashing
from state import nodeState
import configurations as configs

class baseNode:
    def __init__(self, address):
        self._identity      = 0
        self._key            = None
        self._address       = address
        self._running       = True
        self._state         = nodeState.STABLE
        self._storage       = {}
        self._predecessor   = None
        self._fingerTable   = [None]*configs.M_BITS
        self.__successors_stack  = []
        self.__predecessors_stack  = []
        self.__is_stable    = False
        #initial key for  node
        self._key = self._address.__hash__()

        self._fixFingers_thread = threading.Thread()
        self._stabilize_thread = threading.Thread()
        self._checkPredecessor_thread = threading.Thread()

    def this(self):
        result = finger(self._address).this()
        return result

    def dispose(self):
        self._running = False

    def getKeyHash(self, key):
        return consistent_hashing(key)

    def get_key(self):
        return self._address.__hash__()

    def get_identity(self, offset=0):
        return (self._address.__hash__() + offset ) % configs.DHT_SIZE

    def get_address(self):
        return self._address
        
    def running(self):
        return self._running
        
    def is_stable(self):
        return self.__is_stable

    def get_storage(self, index=None):
        storage = self._storage
        if index:
            try:
                result = storage[index]
                return result
            except:
                return None
        return storage

    def set_storage(self, key, value):
        try:
            self._storage[key]=value
            return True
        except:
            return False

    def get_state(self):
        if(self._state == nodeState.STABLE):
            return True
        else:
            return False
        
    def set_state(self, value):
        self._state = value

    def get_predecessor(self):
        pred = self._predecessor
        if (pred != None):
            return pred.this()
        return None
        
    def set_predecessor(self, value):
        self._predecessor = value

    def get_successor(self):
        succ = self._fingerTable[0]
        if (succ != None):
            return succ.this()
        return None
        
    def get_fingertable(self, index=None):
        fingers = self._fingerTable
        result = fingers[index]
        if (result !=None):
            return result.this()
        return None

    def set_fingertable(self, index, value):
        self._fingerTable[index]=value
        return

    def get_node_info(self):
        succ = None
        pred = None

        if (self.get_successor() != None):
            succ = self.get_successor().get_address()
        
        if (self.get_predecessor() != None):
            pred =  self.get_predecessor().get_address()

        node_info = {
                    "node_key": self.get_identity(),
                    "successor": succ,
                    "others": [pred],
                    "sim_crash": not self.get_state(),
                    }
        return node_info

    def get_neighbors(self):
        succ = None
        pred = None
        if (self.get_successor() != None):
            succ = self.get_successor().get_address()
        
        if (self.get_predecessor() != None):
            pred =  self.get_predecessor().get_address()

        l = [succ, pred]
        return [str(x) for x in l if x]

    def get_fingerTables(self):
        l = self.get_fingertable()
        return [str(x.get_address()) for x in l if x]

    def check_address(self, address):
        try:
            conn = http.client.HTTPConnection(address)
            conn.request("GET", "/ping")
            resp = conn.getresponse()
            if resp.status == 200:
                return True
            return False
        except (http.client.HTTPException):
            return False

    def start_workers(self):
        if not self._fixFingers_thread.is_alive():
            self._fixFingers_thread = threading.Thread(target=self.fixFingers)
            self._fixFingers_thread.daemon = True
            self._fixFingers_thread.start()

        if not self._stabilize_thread.is_alive():
            self._stabilize_thread = threading.Thread(target=self.stabilize)
            self._stabilize_thread.daemon = True
            self._stabilize_thread.start()

        if not self._checkPredecessor_thread.is_alive():
            self._checkPredecessor_thread = threading.Thread(target=self.checkPredecessor)
            self._checkPredecessor_thread.daemon = True
            self._checkPredecessor_thread.start()

        self._running = True

    def stop_workers(self):
        self._running = False
        if self._stabilize_thread.is_alive():
            self._stabilize_thread.join()

        if self._checkPredecessor_thread.is_alive():
            self._checkPredecessor_thread.join()

        if self._fixFingers_thread.is_alive():
            self._fixFingers_thread.join()

    def start(self, address=None):
        self.join(address)
        self.start_workers()

    def join(self, address=None):
        self._running = True
        if address:
            if (self.check_address(address) == False):
                print("The remote address not found")
                os._exit(1)

            conn = http.client.HTTPConnection(address)
            conn.request("GET", "/join/"+ str(self.get_identity()))
 
            resp = conn.getresponse()

            if resp.status != 200:
                self.set_fingertable(0, finger(self.get_address()))
            else:
                value = resp.read()
                json_data = json.loads(value)
                self.set_fingertable(0, finger(json_data['address']))
        else:
            self.set_fingertable(0, finger(self.get_address()))
        
        print(self.get_address().__str__() + " joined.")
        self.start_workers()

    def findSuccessor(self, id):
        succ = self.get_successor().get_identity()
        inRange = inrange(int(id), self.get_identity(), succ)
        if (inRange and \
                (self.get_identity() != self.get_successor().get_identity()) and \
                (int(id) != self.get_identity())):

            return self.get_successor()
        else:
            remote = self.closestPrecedingNode(id)
            if self.get_address().__hash__() != remote.get_address().__hash__():
                return self.findSuccessorRemote(remote.get_address(), id)
            else:
                return self.this()

    def closestPrecedingNode(self, id):
        for idx in reversed(range(configs.M_BITS)):
            if self.get_fingertable(idx) != None and \
                    (inrange(self.get_fingertable(idx).get_identity(), self.get_identity(), int(id)) and \
                     (self.get_identity() != int(id)) and \
                     (self.get_fingertable(idx).get_identity() != self.get_identity()) and \
                     (self.get_fingertable(idx).get_identity() != int(id))):
                return self.get_fingertable(idx)

        return self.this()

    def findSuccessorRemote(self, address, id):
        if (self.check_address(str(address)) == False):
            return None

        try:
            conn = http.client.HTTPConnection(address)
            conn.request("GET", "/findsuccessor/" + str(id))
            resp = conn.getresponse()
            conn.close()
            if resp.status != 200:
                return None
            value = resp.read()
            json_data = json.loads(value)
            return finger(json_data['address']).this()
        except:
            return None

    def fixFingers(self):
        i = 0
        while self._running:
            i = i + 1
            if i > configs.M_BITS:
                i = 1
            #self.set_fingertable(i - 1, self.findSuccessor(self.get_identity(2**(i-1))))
            time.sleep(configs.INTERVAL)

    def stabilize(self):
        while self._running:
            # if (self.get_predecessor() != None and self.get_successor() != None):
            #     print("Both successor and predecessor were correctly identified.")

            print("\n")

            if self.get_predecessor() != None:
                print(str(self.get_identity()) + " :: " + "predecessor : ", self.get_predecessor().get_address().__str__(), "id : ",
                      self.get_predecessor().get_identity())
            if self.get_successor() != None:
                print(str(self.get_identity()) + " :: " + "successor : ", self.get_successor().get_address().__str__(), "id : ",
                      self.get_successor().get_identity())

            print("\n")

            suc = self.get_successor()
            if (suc.get_identity() == self.get_identity() and self.get_predecessor() != None):
                self.set_fingertable(0, self.get_predecessor())
            else:
                x = self.findPredecessorRemote(suc.get_address())
                if x != None and \
                        inrange(x.get_identity(), self.get_identity(), suc.get_identity()) and \
                        (self.get_identity() != suc.get_identity()) and \
                        (x.get_identity() != self.get_identity()) and \
                        (x.get_identity() != suc.get_identity()):
                    self.set_fingertable(0, x)
                    self.__is_stable = False
                else:
                    self.__is_stable = True

            self.successor_notify(self.get_address())
            time.sleep(configs.INTERVAL)

    def findPredecessorRemote(self,address):
        if (self.check_address(str(address)) == False):
            return None
            
        try:
            conn = http.client.HTTPConnection(str(address))
            conn.request("GET", "/findpredecessor")
            resp = conn.getresponse()
            conn.close()
            if resp.status != 200:
                return None
            value = resp.read()
            json_data = json.loads(value)
            return finger(json_data['address']).this()
        except (http.client.HTTPException):
            return None

    def successor_notify(self, address):
        if (self.check_address(str(address)) == False):
            return

        conn = http.client.HTTPConnection(str(self.get_successor().get_address()))
        conn.request("POST", "/notify", str(self.get_address()))
        conn.close()

    def notify(self, remote):

        if (self.check_address(str(remote)) == False):
            return

        remote_finger = finger(str(remote))
        if (self.get_predecessor() == None or self.get_predecessor().get_identity() == self.get_identity()) or \
                ((inrange(remote_finger.get_identity(), self.get_predecessor().get_identity(), self.get_identity())) and \
                 (self.get_predecessor().get_identity() != self.get_identity()) and \
                 (remote_finger.get_identity() != self.get_predecessor().get_identity()) and \
                 (remote_finger.get_identity() != self.get_identity())):

            self.set_predecessor(remote_finger.this())
            self.__is_stable = False
        else:
            self.__is_stable = True

    def checkPredecessor(self):
        while self._running:
            if self.get_predecessor() != None:
                if self.get_predecessor().get_address().__hash__() != self.get_address().__hash__():
                    if self.sendPing(self.get_predecessor().get_address()) == False:
                        print("Predecessor '{}' is not alive.".format(self.get_predecessor().get_address()))
                        self.set_predecessor(None)
            time.sleep(configs.INTERVAL)

    def sendPing(self, remote):
        try:
            conn = http.client.HTTPConnection(str(remote))
            conn.request("GET", "/ping")
            resp = conn.getresponse()
            conn.close()
            if resp.status != 200:
                return False
            else:
                return True
        except (http.client.HTTPException):
            return False

    def ping(self):
        return True

    def insertLocalKeyVal(self, key, value):
        hash_key = hash_to_hex(key)
        return self.set_storage(hash_key, value)

    def putKeyValue(self, key, value):
        hashkey = self.getKeyHash(key)
        node = self.findSuccessor(hashkey)
        if node.get_identity() == self.get_identity():
            return self.insertLocalKeyVal(key, value)
        else:
            #if self.get_successor():
            return self.sendPutKeyValue_remote(self.get_successor().get_address(), key, value)
            #else:
             #   return None

    def sendPutKeyValue_remote(self, address, key, value):
        if (self.check_address(str(address)) == False):
            return None

        conn = http.client.HTTPConnection(str(address))
        conn.request("PUT", "/storage/"+key, value)
        resp = conn.getresponse()
        conn.close()
        result = None
        if resp.status == 200:
            result = resp.read()
        return result

    def getKey(self, key):
        hashkey = self.getKeyHash(key)
        node = self.findSuccessor(hashkey)
        if (node.get_identity() == self.get_identity()):
            hash_key = hash_to_hex(key)
            value = self.get_storage(hash_key)
            return value
        else:
            if self.get_successor():
                return self.lookUpKey(key)
            else:
                return None

    def lookUpKey(self, key):
        succ_address= self.get_successor().get_address()
        conn = http.client.HTTPConnection(str(succ_address))
        conn.request("GET", "/storage/" + key)
        resp = conn.getresponse()
        conn.close()
        if resp.status != 200:
            return None
        else:
            value = resp.read()
            return value

    def inform_predecessor(self):
        address = str(self.get_predecessor().get_address())
        if (self.check_address(str(address)) == False):
            return

        conn = http.client.HTTPConnection(address)
        conn.request("POST", "/informPredecessor", str(self.get_successor().get_address()))
        conn.close()

    def inform_successor(self):
        address = str(self.get_successor().get_address())
        if (self.check_address(str(address)) == False):
            return

        conn = http.client.HTTPConnection(address)
        conn.request("POST", "/informSuccessor", str(self.get_predecessor().get_address()))
        conn.close()

    def changePredecessor(self, address):
        pred_node = finger(str(address))
        self.set_predecessor(pred_node)

    def changeSuccessor(self, address):
        succ_node = finger(str(address))
        self.set_fingertable(0,succ_node)

    def put_data(self, address, key, value):
        conn = http.client.HTTPConnection(str(address))
        conn.request("PUT", "/storage/"+key, value)
        conn.close()

    def leave(self):
        self.stop_workers()
        self.inform_predecessor()
        self.inform_successor()
        # for key, value in self.get_storage():
        #     self.put_data(self.get_successor().get_address(), key, value)
        self.set_predecessor(finger(str(self.get_address())))
        self.set_fingertable(0,finger(str(self.get_address())))
