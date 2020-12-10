Distributed Hash Table (DHT)
================================================================
Explnation:
-----------
	- This is a Distributed key-value (DHT) store project based on the Chord protocol. 
	- This system supports Restful architecture as communication betwwen nodes. This means that the nodes are connected to each other by calling the API and exchange json data foramt. 
	- Each node needs a address and port number to run.
	- This system uses the SHA1 hashing algorithm as the main hashing algorithm as well in Consistent Hashing.
	- The current version support dynamic joining and leaving mechanism alongside the simulation crash feature.

Requirements: 
-------------
    System Requirement:
        - python3 (as a programming language)

Steps to setup the project environment:
---------------------------------------
   - 1. configurations.py (the configs file to handle the system bahaviors)
		*** First of all we should set the maximum number (DHT_SIZE) of node that able to be in the network ***
		*** DHT_SIZE is the number obtained by (2 ^ M_BITS) ***
		*** It means that if MBITS = 4, then the maximum number of nodes that can be in the network is 16 ***
		*** The other important variable in config file is INTERVAL Which indicates that the nodes check the stability of the network every few seconds ***
		
	-2. Establish Network
		Run a standalone node: python3 storageNode.py -p 3000
		*** For running a standalone node you can use this. It run a standalone node without connecting to any node ***

		and then we can call other nodes to join the network. Like this:
		python3 storageNode.py -p 3001 localhost:3000
		python3 storageNode.py -p 3002 localhost:3001
		python3 storageNode.py -p 3003 localhost:3000

		or by call the joining API (/join?nprime=localhost:3000)
		
   - 3. python3 test.py : is a test python code which run N standalone nodes (based on DHT_SIZE in configuration.py), and after some seconds, join all that into one network. It is easy way to establish our network alongside testing joining and leaving stability
