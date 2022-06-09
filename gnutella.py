import os, time
import urllib.request
from twisted.internet import reactor, protocol 
from twisted.protocols import basic

from constants import *
import globals
import utility

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
		globals.connections.append(self)
		peer = self.transport.getPeer()
		utility.writeLog("Connected to {0}:{1}\n".format(peer.host, peer.port))
		if self.initiator:
			# global globals.myPort
			x = "GNUTELLA CONNECT/0.4\n{0}\n;".format(globals.myPort)
			self.transport.write(x.encode('utf-8'))
			utility.writeLog("Sending GNUTELLA CONNECT to {0}:{1}\n".format(peer.host, peer.port))
		host = self.transport.getHost()
		# global globals.myIP
		print('line 35', globals.myIP)
		globals.myIP = host.host
		print('line 37', globals.myIP)

	def connectionLost(self, reason):
		globals.connections.remove(self)
		peer = self.transport.getPeer()
		utility.writeLog("Disconnected with {0}:{1}\n".format(peer.host, peer.port))
		utility.makePeerConnection()

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
			utility.writeLog("Received GNUTELLA CONNECT from {0}:{1}\n".format(peer.host, peer.port))
			if(len(globals.connections) <= MAX_CONNS):
				# global globals.myPort
				self.transport.write("GNUTELLA OK\n{0}\n;".format(globals.myPort).encode('utf-8'))
				utility.writeLog("Sending GNUTELLA OK to {0}:{1}\n".format(peer.host, peer.port))
			else:
				self.transport.write("WE'RE OUT OF NUTELLA\n;".encode('utf-8'))
				utility.writeLog("Sending WE'RE OUT OF NUTELLA to {0}:{1}\n".format(peer.host, peer.peer))
		elif (self.initiator and not self.verified):
			if(data.startswith("GNUTELLA OK")):
				self.peerPort = int(data.split('\n')[1])
				utility.writeLog("Connection with {0}:{1} verified\n".format(peer.host, peer.port))
				self.verified = True
				self.sendPing()
			else:
				utility.writeLog("Connection with {0}:{1} rejected\n".format(peer.host, peer.port))
				reactor.stop()
		else:
			#writeLog("\nIncoming message: {0}\n".format(data))
			utility.writeLog("\n")
			message = data.split('&', 3)
			msgid = message[0]
			payloadDesc = int(message[1])
			ttl = int(message[2])
			payload = message[3]
			if(payloadDesc == 0):
				utility.writeLog("Received PING: msgid={0} ttl={1}\n".format(msgid, ttl))
				self.handlePing(msgid, ttl)
			elif(payloadDesc == 1):
				utility.writeLog("Received PONG: msgid={0} payload={1}\n".format(msgid, payload))
				self.handlePong(msgid, payload)
			elif(payloadDesc == 80):
				utility.writeLog("Received Query: msgid={0} ttl={1} query={2}\n".format(msgid, ttl, payload))
				self.handleQuery(msgid, ttl, payload)
			elif(payloadDesc == 81):
				utility.writeLog("Received QueryHit: msgid={0} payload={1}\n".format(msgid, payload))
				self.handleQueryHit(msgid, payload)

	def buildHeader(self, descrip, ttl):
		# global globals.msgID
		header = "{0}{1:03}".format(globals.nodeID, globals.msgID)
		globals.msgID += 1
		if(globals.msgID > 999):
			globals.msgID = 0
		return "{0}&{1}&{2}&".format(header, descrip, ttl) 

	def sendPing(self, msgid=None, ttl=7):
		if(ttl <= 0):
			return
		if msgid:
			message = "{0}&{1}&{2}&".format(msgid, "00", ttl)
			utility.writeLog("Forwarding PING: {0}\n".format(message))
		else:
			message = self.buildHeader("00", ttl)
			utility.writeLog("Sending PING: {0}\n".format(message))
		message = "{0};".format(message)
		for cn in globals.connections:
			if(msgid == None or cn != self):
				cn.transport.write(message.encode('utf-8'))

	def sendPong(self, msgid, payload=None):
		nfiles = 0
		nkb = 0
		# global globals.myPort
		IP = self.transport.getHost().host
		header = "{0}&{1}&{2}&".format(msgid, "01", 7)
		if payload:
			message = "{0}{1};".format(header, payload)
			utility.writeLog("Forwarding PONG: {0}\n".format(message))
		else: 
			#message = "{0}{1}&{2}&{3}&{4};".format(header, globals.port, IP, nfiles, nkb)
			message = "{0}{1}&{2};".format(header, globals.myPort, IP)
			utility.writeLog("Sending PONG: {0}\n".format(message))
		# global globals.msgRoutes
		globals.msgRoutes[msgid][0].transport.write(message.encode('utf-8'))

	def handlePing(self, msgid, ttl):
		#send pong, store data, forward ping
		if utility.isValid(msgid):
			return
		# global globals.msgRoutes
		globals.msgRoutes[msgid] = (self, time.time())
		self.sendPong(msgid)
		self.sendPing(msgid, ttl-1)

	def handlePong(self, msgid, payload):
		# global globals.nodeID
		# global globals.netData
		info = payload.split("&")
		node_data = (int(info[0]), info[1])
		if info not in globals.netData:
			globals.netData.append(node_data)
		if(msgid.startswith(globals.nodeID)):
			utility.makePeerConnection(node_data[1], node_data[0])
		else:
			self.sendPong(msgid, payload)
			utility.makePeerConnection()

	def sendQuery(self, query, msgid=None, ttl=7):
		if(ttl <= 0):
			return
		if(msgid):
			header = "{0}&80&{1}&".format(msgid, ttl)
		else:
			header = self.buildHeader(80, ttl)
		message = "{0}{1};".format(header, query)
		# global globals.connections
		for cn in globals.connections:
			if(msgid == None or cn != self):
				cn.transport.write(message.encode('utf-8'))

	def sendQueryHit(self, msgid, query=None, payload=None):
		header = "{0}&81&7&".format(msgid)
		# global globals.msgRoutes
		if not utility.isValid(msgid):
			return
		if payload:
			message = "{0}{1};".format(header, payload)
		else:
			# global globals.myIP
			# global globals.serverPort
			message = "{0}{1}&{2}&{3};".format(header, globals.myFileServerPort, globals.myIP, query)
		globals.msgRoutes[msgid][0].transport.write(message.encode('utf-8'))

	def handleQuery(self, msgid, ttl, query):
		# global globals.msgRoutes
		if utility.isValid(msgid):
			return
		globals.msgRoutes[msgid] = (self, time.time())
		# global globals.directory
		if "../" in query:
			print("Cannot request files in upper directories")
			return
		filepath = os.path.join(globals.directory, query)
		if os.path.isfile(filepath):
			self.sendQueryHit(msgid, query=query)
			utility.writeLog("File found: {0}; Sending QueryHit\n".format(query))
		else:
			self.sendQuery(query, msgid, ttl-1)
			utility.writeLog("Forwarding Query: {0} {1}".format(query, msgid))

	def handleQueryHit(self, msgid, payload):
		# global globals.nodeID
		if(msgid.startswith(globals.nodeID)):
			info = payload.split('&', 2)
			port = info[0]
			ip = info[1]
			query = info[2]
			print("Found port, ip, file: ", info)
			# global globals.directory
			filepath = os.path.join(globals.directory, query)
			if not os.path.isfile(filepath):
				utility.printLine("Getting file \"{0}\" from {1}:{2}".format(query, ip, port)) 
				reactor.callInThread(self.getFile, port, ip, query, filepath)
		else:
			self.sendQueryHit(msgid, payload=payload)

	def getFile(self, port, ip, query, filepath):
		url = "http://{0}:{1}/{2}".format(ip, port, query)
		fp = open(filepath, "w")
		fp.write(bytes.decode(urllib.request.urlopen(url).read()))
		fp.close()


class GnutellaFactory(protocol.ReconnectingClientFactory):
	def __init__(self, isInitiator=False):
		self.initiator = isInitiator

	def buildProtocol(self, addr):
		prot = GnutellaProtocol()
		if self.initiator:
			prot.setInitiator()
		return prot
 
	def startedConnecting(self, connector):
		self.host = connector.host
		self.port = connector.port
		utility.writeLog("Trying to connect to {0}:{1}\n".format(self.host, self.port))

	def clientConnectionFailed(self, transport, reason):
		utility.writeLog("Retrying connection with %s:%s\n" % (transport.host, transport.port))
		# global globals.connections
		numConns = len(globals.connections)
		if numConns == 0:
			utility.makePeerConnection()
