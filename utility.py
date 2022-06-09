import random, time, re
from twisted.internet import reactor

from constants import *
# from globals import *
import globals
from gnutella import GnutellaFactory

"""
GLOBAL HELPER FUNCTIONS
"""
def makePeerConnection(IP=None, port=None):
	global MAX_CONNS
	# global globals.netData
	# global globals.connections
	cleanPeerList()
	numConns = len(globals.connections)
	if (numConns < MAX_CONNS and len(globals.netData) > 0):
		if numConns == 0 or shouldConnect(numConns):
			randNode = globals.netData[random.randint(0, len(globals.netData)-1)]
			if (not IP and not port):
				IP = randNode[1] 
				port = randNode[0]
				globals.netData.remove(randNode)
			reactor.connectTCP(IP, port, GnutellaFactory(True))

def shouldConnect(numConns):
	global MIN_CONNS
	global UNDER_PROB
	global OVER_PROB
	prob = random.randint(0, 99)
	if (numConns < MIN_CONNS):
		if (prob < UNDER_PROB):
			return True
	elif (prob < OVER_PROB):
			return True
	return False

def cleanPeerList():
	# global globals.netData
	# global globals.connections
	for conn in globals.connections:
		peer = conn.transport.getPeer()
		peer_info = (conn.peerPort, peer.host)
		if peer_info in globals.netData:
			globals.netData.remove(peer_info)

def readInput():
	# global globals.connections
	print("Requests files with \"GET [filename];\"")
	pattern = re.compile("GET\s+(.+);$")
	while(1):
		request = input()
		match = pattern.match(request)
		if(match):
			query = match.group(1)
			if (len(globals.connections) > 0):
				globals.connections[0].sendQuery(query)
			else:
				print("No other nodes in network at the moment") 
		elif(request.startswith("QUIT")):
			return
		else:
			print("Requests must be in the format \"GET [filename];\"\n")

def writeLog(line):
	# global globals.logFile
	globals.logFile = open(globals.logPath, "a")
	globals.logFile.write(line)
	globals.logFile.close()

def printLine(line):
	print(line)
	writeLog("{0}\n".format(line))

def isValid(msgid):
	# global globals.msgRoutes
	global msgTimeout
	now = time.time()
	if msgid in globals.msgRoutes.keys() and now - globals.msgRoutes[msgid][1] < MSG_TIMEOUT:
		globals.msgRoutes[msgid] = (globals.msgRoutes[msgid][0], now)
		return True
	return False