import sys, socket, os
from uuid import getnode as getmac
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor

# from globals import *
import globals
from utility import printLine, readInput
from gnutella import GnutellaFactory

"""
MAIN FUNCTION
"""

if __name__=="__main__":
	args = sys.argv[1:]
	hasIP = False
	hasPort = False
	#must redeclare variables as globals within function
	#otherwise, python recreates a local variable 
	targetIP = None
	targetPort = None
	for arg in args:
		if(arg == "-i"):
			hasIP = True
		elif(arg == "-p"):
			hasPort = True
		elif(hasIP):
			targetIP = arg
			hasIP = False
		elif(hasPort):
			targetPort = int(arg)
			hasPort = False
		else:
			globals.directory = arg

	if globals.directory:
		#Set up directories and log file
		if not os.path.isdir(globals.directory):
			os.makedirs(globals.directory)
		globals.logPath = os.path.join(globals.directory,"output.log")
		open(globals.logPath, "w").close() #Create or empty current log file
		globals.directory = os.path.join(globals.directory, 'files')
		if not os.path.exists(globals.directory):
			os.makedirs(globals.directory)
		print("Run \"tail -c +0 -f {0}\" in another terminal to see output".format(globals.logPath))
		printLine("Using directory: {0}".format(globals.directory))

		#Set up Twisted clients
		if(targetIP and targetPort):
			print(reactor.connectTCP(targetIP, targetPort, GnutellaFactory(True)))
		
		usedPort = reactor.listenTCP(globals.myPort, GnutellaFactory(), interface=socket.gethostbyname(socket.gethostname()))
		host = usedPort.getHost()
		globals.myIP = host.host
		globals.myPort = host.port
		globals.nodeID = "{0}{1:05}".format(getmac(), globals.myPort)
		printLine("IP address: {0}:{1}".format(globals.myIP, globals.myPort))
		resource = File(globals.directory)
		fileServer = reactor.listenTCP(0, Site(resource))
		globals.myFileServerPort = fileServer.getHost().port
		printLine("File serving port: {0}".format(globals.myFileServerPort))
		printLine("Node ID: {0}".format(globals.nodeID))
		reactor.callInThread(readInput)
		reactor.run()
		globals.logFile.close()
	else:
		print("Must give a directory path")
