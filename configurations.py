#!/usr/bin/env python3

#Configurations items
#--------------------------------------------------------------------------------
#KEY                        VALUE               DESCRIPTION
#--------------------------------------------------------------------------------
M_BITS                      = 2
DHT_SIZE                    = (2**M_BITS)       # Maximum nodes can be in network
DEFAULT_PORT                = 49152
START_PORT_FROM             = DEFAULT_PORT
PORT_NUMBER_RANGE           = 65535
DIE_AFTER_SECONDS_DEFAULT   = 3 * 60            # kill server after this seconds
INTERVAL                    = 1                 # in seconds
