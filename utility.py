import random, time, re
from twisted.internet import reactor

from constants import *
from globals import *
from gnutella import GnutellaFactory

"""
GLOBAL HELPER FUNCTIONS
"""
def makePeerConnection(IP=None, port=None):
  global MAX_CONNS
  global netData
  global connections
  cleanPeerList()
  numConns = len(connections)
  if (numConns < MAX_CONNS and len(netData) > 0):
    if numConns == 0 or shouldConnect(numConns):
      randNode = netData[random.randint(0, len(netData)-1)]
      if (not IP and not port):
        IP = randNode[1] 
        port = randNode[0]
        netData.remove(randNode)
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
  global netData
  global connections
  for conn in connections:
    peer = conn.transport.getPeer()
    peer_info = (conn.peerPort, peer.host)
    if peer_info in netData:
      netData.remove(peer_info)

def readInput():
  global connections
  print("Requests files with \"GET [filename];\"")
  pattern = re.compile("GET\s+(.+);$")
  while(1):
    request = input()
    match = pattern.match(request)
    if(match):
      query = match.group(1)
      if (len(connections) > 0):
        connections[0].sendQuery(query)
      else:
        print("No other nodes in network at the moment") 
    elif(request.startswith("QUIT")):
      return
    else:
      print("Requests must be in the format \"GET [filename];\"\n")

def writeLog(line):
  global logFile
  logFile = open(logPath, "a")
  logFile.write(line)
  logFile.close()

def printLine(line):
  print(line)
  writeLog("{0}\n".format(line))

def isValid(msgid):
  global msgRoutes
  global msgTimeout
  now = time.time()
  if msgid in msgRoutes.keys() and now - msgRoutes[msgid][1] < MSG_TIMEOUT:
    msgRoutes[msgid] = (msgRoutes[msgid][0], now)
    return True
  return False