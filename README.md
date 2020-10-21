INF3200: Distributed Systems Fundamentals Mandatory Assignment 1
UiT the Arctic University of Norway
================================================================

Team members:
	-Amin Ziagham Ahwazi {azi011@uit.no}
	-Keerthana Sivakumar {ksi055@uit.no}

Explnation:
-----------
	- This is a Distributed key-value (DHT) store project based on the Chord protocol. 
	- This system supports Restful architecture as communication betwwen nodes. This means that the nodes are connected to each other by calling the API and exchange json data foramt. 
	- Each node needs a address and port number to run.
	- This system uses the SHA1 hashing algorithm as the main hashing algorithm as well in Consistent Hashing.

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
		python3 storageNode.py -p 3000 : at first it must be execute in order to established an initial network
		*** Note that the first node must be run alone, in order to stablish the network ***
		
		and then we can call other nodes to join the network. Like this:
		python3 storageNode.py -p 3001 localhost:3000
		python3 storageNode.py -p 3002 localhost:3001
		python3 storageNode.py -p 3003 localhost:3000
		...
		
   - 3. terminal.py localhost:3000 : address of any of DHT nodes in order to send lookUp() or putData() in the network.
		*** this is a sample console app than can run to manage and monitoring the network ***