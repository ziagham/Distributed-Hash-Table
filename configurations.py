#!/usr/bin/env python3

#description "INF3200: Distributed Systems Fundamentals Mandatory Assignment 1"
#authors    [
#               {"Name": "Amin Ziagham Ahwazi", "Email":"azi011@uit.no"}, 
#               {"Name": "Keerthana Sivakumar", "Email":"ksi055@uit.no"}
#           ]

#Configurations items
#--------------------------------------------------------------------------------
#KEY                        VALUE               DESCRIPTION
#--------------------------------------------------------------------------------
M_BITS                      = 1
DHT_SIZE                    = (2**M_BITS)       # Maximum nodes can be in network
DEFAULT_PORT                = 49152
DIE_AFTER_SECONDS_DEFAULT   = 2 * 60           # kill server after this seconds
INTERVAL                    = 1                 # in seconds