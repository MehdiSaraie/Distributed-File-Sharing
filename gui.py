import sys, socket, os
from uuid import getnode as getmac
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from threading import Thread
from netifaces import interfaces, ifaddresses, AF_INET

import globals
from utility import printLine
from gnutella import GnutellaFactory

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *


class Ui_MainWindow(QtCore.QObject, object):
	socketSignal = QtCore.pyqtSignal(str)

	def setupUi(self, MainWindow):
		MainWindow.setObjectName("MainWindow")
		MainWindow.resize(800, 600)
		self.centralwidget = QWidget(MainWindow)
		self.centralwidget.setObjectName("centralwidget")

		self.openSharingDirectoryButton = QPushButton(self.centralwidget)
		self.openSharingDirectoryButton.setGeometry(QtCore.QRect(40, 60, 160, 30))
		self.openSharingDirectoryButton.setText("Open Sharing Directory")
		self.openSharingDirectoryButton.setObjectName("openSharingDirectory")
		self.openSharingDirectoryButton.clicked.connect(lambda : self.openSharingDirectory())
		self.changeSharingDirectoryButton = QPushButton(self.centralwidget)
		self.changeSharingDirectoryButton.setGeometry(QtCore.QRect(230, 60, 160, 30))
		self.changeSharingDirectoryButton.setText("Change Sharing Directory")
		self.changeSharingDirectoryButton.setObjectName("changeSharingDirectory")
		self.changeSharingDirectoryButton.clicked.connect(lambda : self.changeSharingDirectory())
		self.fileNameLabel = QLabel(self.centralwidget)
		self.fileNameLabel.setGeometry(QtCore.QRect(40, 120, 100, 30))
		self.fileNameLabel.setObjectName("fileNameLabel")
		self.fileNameLineEdit = QLineEdit(self.centralwidget)
		self.fileNameLineEdit.setGeometry(QtCore.QRect(110, 120, 220, 28))
		self.fileNameLineEdit.setObjectName("fileNameLineEdit")
		self.downloadButton = QPushButton(self.centralwidget)
		self.downloadButton.setGeometry(QtCore.QRect(360, 120, 30, 30))
		self.downloadButton.setText("")
		self.downloadButton.setObjectName("download")
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap("download.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.downloadButton.setIcon(icon)
		self.downloadButton.setIconSize(QtCore.QSize(20, 20))
		self.downloadButton.clicked.connect(lambda : self.sendQuery())
		self.progressBar = QProgressBar(self.centralwidget)
		self.progressBar.setGeometry(QtCore.QRect(35, 520, 300, 23))
		self.progressBar.setValue(0)
		self.progressBar.setTextVisible(True)
		self.progressBar.setObjectName("progressBar")
		self.speedLabel = QLabel(self.centralwidget)
		self.speedLabel.setGeometry(QtCore.QRect(360, 520, 80, 21))
		self.speedLabel.setObjectName("speedLabel")

		self.peersListWidget = QListWidget(self.centralwidget)
		self.peersListWidget.setGeometry(QtCore.QRect(460, 100, 261, 192))
		self.peersListWidget.setObjectName("peersList")
		self.peersLabel = QLabel(self.centralwidget)
		self.peersLabel.setGeometry(QtCore.QRect(570, 30, 51, 21))
		font = QtGui.QFont()
		font.setPointSize(10)
		font.setBold(True)
		font.setWeight(75)
		self.peersLabel.setFont(font)
		self.peersLabel.setTextFormat(QtCore.Qt.AutoText)
		self.peersLabel.setObjectName("peers")
		self.ipLineEdit = QLineEdit(self.centralwidget)
		self.ipLineEdit.setGeometry(QtCore.QRect(470, 70, 121, 22))
		self.ipLineEdit.setInputMask("")
		self.ipLineEdit.setText("")
		self.ipLineEdit.setObjectName("ip")
		self.portLineEdit = QLineEdit(self.centralwidget)
		self.portLineEdit.setGeometry(QtCore.QRect(610, 70, 61, 22))
		self.portLineEdit.setText("")
		self.portLineEdit.setObjectName("port")
		self.addConnectionButton = QPushButton(self.centralwidget)
		self.addConnectionButton.setGeometry(QtCore.QRect(690, 70, 21, 20))
		self.addConnectionButton.setText("")
		icon1 = QtGui.QIcon()
		icon1.addPixmap(QtGui.QPixmap("add_connection.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
		self.addConnectionButton.setIcon(icon1)
		self.addConnectionButton.setIconSize(QtCore.QSize(28, 28))
		self.addConnectionButton.setObjectName("addConnection")
		self.addConnectionButton.clicked.connect(lambda : self.addConnection(self.ipLineEdit.text(), int(self.portLineEdit.text())))

		MainWindow.setCentralWidget(self.centralwidget)
		self.menubar = QMenuBar(MainWindow)
		self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 26))
		self.menubar.setObjectName("menubar")
		MainWindow.setMenuBar(self.menubar)
		self.statusbar = QStatusBar(MainWindow)
		self.statusbar.setObjectName("statusbar")
		MainWindow.setStatusBar(self.statusbar)

		self.retranslateUi(MainWindow)
		QtCore.QMetaObject.connectSlotsByName(MainWindow)
		self.socketSignal.connect(self.executeOnMain)

	def retranslateUi(self, MainWindow):
		_translate = QtCore.QCoreApplication.translate
		MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
		self.fileNameLabel.setText(_translate("MainWindow", "File Name:"))
		self.peersLabel.setText(_translate("MainWindow", "Peers"))
		self.ipLineEdit.setPlaceholderText(_translate("MainWindow", " IP"))
		self.portLineEdit.setPlaceholderText(_translate("MainWindow", " Port"))
		self.speedLabel.setText(_translate("MainWindow", ""))
	
	def executeOnMain(self, data):
		info = data.split("&")
		if info[0] == "updateProgressBar":
			value, speed = int(info[1]), info[2]
			self.updateProgressBar(value, speed)

	def openSharingDirectory(self):
		filepath, _ = QFileDialog.getOpenFileName(self.centralwidget, "Select File", globals.directory)
		if (filepath):
			os.startfile(filepath)

	def changeSharingDirectory(self):
		directory = QFileDialog.getExistingDirectory(self.centralwidget, "Select Directory", globals.directory)
		if (directory):
			globals.directory = directory

	"""
	interface to gnutella functions
	"""
	def addConnection(self, targetIP, targetPort):
		reactor.connectTCP(targetIP, targetPort, GnutellaFactory(True))
		self.ipLineEdit.setText("")
		self.portLineEdit.setText("")

	def sendQuery(self):
		query = self.fileNameLineEdit.text()
		print(query)
		filepath = os.path.join(globals.directory, query)
		if not os.path.isfile(filepath):
			if (len(globals.connections) > 0):
				globals.connections[0].sendQuery(query)
			else:
				printLine("No other nodes in network at the moment")
		else:
			print("File already exists; No need to download")

	"""
	gnutella to interface functions
	"""
	def addPeerToListWidget(self, ip, port):
		self.peersListWidget.addItem(ip + ":" + str(port))

	def removePeerFromListWidget(self, ip, port):
		for i in range(self.peersListWidget.count()):
			item = self.peersListWidget.item(i)
			if item.text() == ip + ":" + str(port):
				self.peersListWidget.takeItem(self.peersListWidget.row(item))
				break

	def updateProgressBar(self, value, speed):
		self.progressBar.setValue(value)
		self.speedLabel.setText(str(speed) + " bps")

def showWindow():
	app = QApplication(sys.argv)
	MainWindow = QMainWindow()
	globals.ui = Ui_MainWindow()
	globals.ui.setupUi(MainWindow)
	MainWindow.show()
	sys.exit(app.exec_())

def getMyIP():
	for ifaceName in interfaces():
		for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}]):
			if i['addr'].startswith('192'):
				return i['addr']

if __name__ == "__main__":
	globals.directory = '.'
	if globals.directory:
		#Set up directories and log file
		if not os.path.isdir(globals.directory):
			os.makedirs(globals.directory)
		globals.logPath = os.path.join(globals.directory,"output.log")
		open(globals.logPath, "w").close() #Create or empty current log file
		globals.directory = os.path.join(globals.directory, 'files')
		if not os.path.exists(globals.directory):
			os.makedirs(globals.directory)
		printLine("Using directory: {0}".format(globals.directory))
		
		usedPort = reactor.listenTCP(globals.myPort, GnutellaFactory(), interface=getMyIP())
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
		Thread(target=reactor.run, args=(False,)).start()
		showWindow()
	else:
		print("Must give a directory path")
