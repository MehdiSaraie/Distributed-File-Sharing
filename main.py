import sys, socket
from uuid import getnode as getmac
from twisted.web.server import Site
from twisted.web.static import File

from gnutella import *

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
      directory = arg

  if directory:
    #Set up directories and log file
    if not os.path.isdir(directory):
      os.makedirs(directory)
    logPath = os.path.join(directory,"output.log")
    open(logPath, "w").close() #Create or empty current log file
    directory = os.path.join(directory, 'files')
    if not os.path.exists(directory):
      os.makedirs(directory)
    print("Run \"tail -c +0 -f {0}\" in another terminal to see output".format(logPath))
    printLine("Using directory: {0}".format(directory))

    #Set up Twisted clients
    print(targetIP)
    print(targetPort)
    if(targetIP and targetPort):
      print(reactor.connectTCP(targetIP, targetPort, GnutellaFactory(True)))
      
    listener = GnutellaFactory()
    usedPort = reactor.listenTCP(port, listener, interface=socket.gethostbyname(socket.gethostname()))
    host = usedPort.getHost()
    IP = host.host
    port2 = host.port
    print("hehe", IP, port2)
    nodeID = "{0}{1:05}".format(getmac(), port2)
    printLine("IP address: {0}:{1}".format(host.host, host.port))
    resource = File(directory)
    fileServer = reactor.listenTCP(0, Site(resource))
    serverPort = fileServer.getHost().port
    printLine("File serving port: {0}".format(serverPort))
    printLine("Node ID: {0}".format(nodeID))
    reactor.callInThread(readInput)
    reactor.run()
    logFile.close()
  else:
    print("Must give a directory path")
