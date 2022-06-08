import os
import urllib.request
from twisted.internet import reactor, protocol 
from twisted.protocols import basic

from utility import *

"""
GNUTELLA TWISTED CLASSES
"""
class GnutellaProtocol(basic.LineReceiver):
  def __init__(self):
    self.output = None
    self.normalizeNewlines = True
    self.initiator = False
    self.verified = True

  def setInitiator(self):
    self.initiator = True
    self.verified = False

  def connectionMade(self):
    connections.append(self)
    peer = self.transport.getPeer()
    writeLog("Connected to {0}:{1}\n".format(peer.host, peer.port))
    if self.initiator:
      global port
      x = "GNUTELLA CONNECT/0.4\n{0}\n;".format(port)
      self.transport.write(x.encode('utf-8'))
      writeLog("Sending GNUTELLA CONNECT to {0}:{1}\n".format(peer.host, peer.port))
    host = self.transport.getHost()
    global IP
    IP = host.host

  def connectionLost(self, reason):
    connections.remove(self)
    peer = self.transport.getPeer()
    writeLog("Disconnected with {0}:{1}\n".format(peer.host, peer.port))
    makePeerConnection()

  def dataReceived(self, data):
    data = bytes.decode(data)
    peer = self.transport.getPeer()
    #writeLog("\nData received from %s: %s" % (peer.port, data))
    lines = data.split(";")
    for line in lines:
      if (len(line) > 0):
        print(line)
        self.handleMessage(line)

  def handleMessage(self, data):
    peer = self.transport.getPeer()
    if(data.startswith("GNUTELLA CONNECT")):
      self.peerPort = int(data.split('\n')[1])
      writeLog("Received GNUTELLA CONNECT from {0}:{1}\n".format(peer.host, peer.port))
      if(len(connections) <= MAX_CONNS):
        global port
        self.transport.write("GNUTELLA OK\n{0}\n;".format(port).encode('utf-8'))
        writeLog("Sending GNUTELLA OK to {0}:{1}\n".format(peer.host, peer.port))
      else:
        self.transport.write("WE'RE OUT OF NUTELLA\n;".encode('utf-8'))
        writeLog("Sending WE'RE OUT OF NUTELLA to {0}:{1}\n".format(peer.host, peer.peer))
    elif (self.initiator and not self.verified):
      if(data.startswith("GNUTELLA OK")):
        self.peerPort = int(data.split('\n')[1])
        writeLog("Connection with {0}:{1} verified\n".format(peer.host, peer.port))
        self.verified = True
        self.sendPing()
      else:
        writeLog("Connection with {0}:{1} rejected\n".format(peer.host, peer.port))
        reactor.stop()
    else:
      #writeLog("\nIncoming message: {0}\n".format(data))
      writeLog("\n")
      message = data.split('&', 3)
      msgid = message[0]
      pldescrip = int(message[1])
      ttl = int(message[2])
      payload = message[3]
      if(pldescrip == 0):
        writeLog("Received PING: msgid={0} ttl={1}\n".format(msgid, ttl))
        self.handlePing(msgid, ttl)
      elif(pldescrip == 1):
        writeLog("Received PONG: msgid={0} payload={1}\n".format(msgid, payload))
        self.handlePong(msgid, payload)
      elif(pldescrip == 80):
        writeLog("Received Query: msgid={0} ttl={1} query={2}\n".format(msgid, ttl, payload))
        self.handleQuery(msgid, ttl, payload)
      elif(pldescrip == 81):
        writeLog("Received QueryHit: msgid={0} payload={1}\n".format(msgid, payload))
        self.handleQueryHit(msgid, payload)

  def buildHeader(self, descrip, ttl):
    global msgID
    header = "{0}{1:03}".format(nodeID, msgID)
    msgID += 1
    if(msgID > 999):
      msgID = 0
    return "{0}&{1}&{2}&".format(header, descrip, ttl) 

  def sendPing(self, msgid=None, ttl=7):
    if(ttl <= 0):
      return
    if msgid:
      message = "{0}&{1}&{2}&".format(msgid, "00", ttl)
      writeLog("Forwarding PING: {0}\n".format(message))
    else:
      message = self.buildHeader("00", ttl)
      writeLog("Sending PING: {0}\n".format(message))
    message = "{0};".format(message)
    for cn in connections:
      if(msgid == None or cn != self):
        cn.transport.write(message.encode('utf-8'))

  def sendPong(self, msgid, payload=None):
    nfiles = 0
    nkb = 0
    global port
    IP = self.transport.getHost().host
    header = "{0}&{1}&{2}&".format(msgid, "01", 7)
    if payload:
      message = "{0}{1};".format(header, payload)
      writeLog("Forwarding PONG: {0}\n".format(message))
    else: 
      #message = "{0}{1}&{2}&{3}&{4};".format(header, port, IP, nfiles, nkb)
      message = "{0}{1}&{2};".format(header, port, IP)
      writeLog("Sending PONG: {0}\n".format(message))
    global msgRoutes
    msgRoutes[msgid][0].transport.write(message.encode('utf-8'))

  def handlePing(self, msgid, ttl):
    #send pong, store data, forward ping
    if isValid(msgid):
      return
    global msgRoutes
    msgRoutes[msgid] = (self, time.time())
    self.sendPong(msgid)
    self.sendPing(msgid, ttl-1)

  def handlePong(self, msgid, payload):
    global nodeID
    global netData
    info = payload.split("&")
    node_data = (int(info[0]), info[1])
    if info not in netData:
      netData.append(node_data)
    if(msgid.startswith(nodeID)):
      makePeerConnection(node_data[1], node_data[0])
    else:
      self.sendPong(msgid, payload)
      makePeerConnection()

  def sendQuery(self, query, msgid=None, ttl=7):
    if(ttl <= 0):
      return
    if(msgid):
      header = "{0}&80&{1}&".format(msgid, ttl)
    else:
      header = self.buildHeader(80, ttl)
    message = "{0}{1};".format(header, query)
    global connections
    for cn in connections:
      if(msgid == None or cn != self):
        cn.transport.write(message.encode('utf-8'))

  def sendQueryHit(self, msgid, query=None, payload=None):
    header = "{0}&81&7&".format(msgid)
    global msgRoutes
    if not isValid(msgid):
      return
    if payload:
      message = "{0}{1};".format(header, payload)
    else:
      global IP
      global serverPort
      message = "{0}{1}&{2}&{3};".format(header, serverPort, IP, query)
    msgRoutes[msgid][0].transport.write(message.encode('utf-8'))

  def handleQuery(self, msgid, ttl, query):
    global msgRoutes
    if isValid(msgid):
      return
    msgRoutes[msgid] = (self, time.time())
    global directory
    if "../" in query:
      print("Cannot request files in upper directories")
      return
    filepath = os.path.join(directory, query)
    if os.path.isfile(filepath):
      self.sendQueryHit(msgid, query=query)
      writeLog("File found: {0}; Sending QueryHit\n".format(query))
    else:
      self.sendQuery(query, msgid, ttl-1)
      writeLog("Forwarding Query: {0} {1}".format(query, msgid))

  def handleQueryHit(self, msgid, payload):
    global nodeID
    if(msgid.startswith(nodeID)):
      info = payload.split('&', 2)
      port = info[0]
      ip = info[1]
      query = info[2]
      print("Found port, ip, file: ", info)
      global directory
      filepath = os.path.join(directory, query) 
      if os.path.isfile(filepath):
        printLine("Getting file \"{0}\" from {1}:{2}".format(query, ip, port)) 
        reactor.callInThread(self.getFile, port, ip, query, filepath)
    else:
      self.sendQueryHit(msgid, payload=payload)

  def getFile(self, port, ip, query, filepath):
    request = os.path.join(port, query)
    url = "http://{0}:{1}".format(ip, request)
    fp = open(filepath, "w")
    fp.write(bytes.decode(urllib.request.urlopen(url).read()))
    fp.close()


class GnutellaFactory(protocol.ReconnectingClientFactory):
  def __init__(self, isInitiator=False):
    self.initiator = False
    if isInitiator:
      self.initiator = True

  def buildProtocol(self, addr):
    prot = GnutellaProtocol()
    if self.initiator:
      prot.setInitiator()
    return prot
 
  def startedConnecting(self, connector):
    self.host = connector.host
    self.port = connector.port
    writeLog("Trying to connect to {0}:{1}\n".format(self.host, self.port))

  def clientConnectionFailed(self, transport, reason):
    writeLog("Retrying connection with %s:%s\n" % (transport.host, transport.port))
    global connections
    numConns = len(connections)
    if numConns == 0:
      makePeerConnection()
