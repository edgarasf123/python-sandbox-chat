from sandbox_chat import Menu, ChatTcp
from PyQt5.QtWidgets import QWidget, QGridLayout, QTextBrowser, QLineEdit, QVBoxLayout, QGroupBox, QCheckBox, QRadioButton
from PyQt5.QtGui import QColor, QTextCursor 
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject


import socket
import threading
import socketserver
import logging


class MenuChat(Menu):
    
    def __init__(self):
        Menu.__init__(self, "Chat")
        
        self.widget = QWidget()
        
        self.hosts = {}
        
        qtMainLayout = QGridLayout(self.widget)
        qtText = QTextBrowser()
        qtInput = QLineEdit()
        
        qtConfigLayout = QVBoxLayout()
        
        qtHosts = QGroupBox("Recipients")
        qtHostsLayout = QVBoxLayout(qtHosts)
        
        
        def onBroadcastChange(state):
            self.setBroadcast(state>0)
            
        qtBroadcast = QCheckBox("Broadcast")
        qtBroadcast.stateChanged.connect(onBroadcastChange)
        
        
        qtNetworkBox = QGroupBox("Network")
        qtNetworkLayout = QVBoxLayout(qtNetworkBox)
        
        def onNetworkChange():
            if self.qtNetworkTCP.isChecked():
                self.qtHosts.setEnabled(True)
                
                self.qtBroadcast.setEnabled(False)
                self.qtBroadcast.setCheckState(0)
            elif self.qtNetworkUDP.isChecked():
                self.qtBroadcast.setEnabled(True)
                
            
        qtNetworkTCP = QRadioButton("TCP")
        qtNetworkUDP = QRadioButton("UDP")
        qtNetworkLayout.addWidget(qtNetworkUDP)
        qtNetworkLayout.addWidget(qtNetworkTCP)
        
        qtNetworkUDP.toggle()
        
        qtConfigLayout.addWidget(qtBroadcast)
        qtConfigLayout.addWidget(qtHosts)
        qtConfigLayout.addWidget(qtNetworkBox)
        
        qtMainLayout.addWidget(qtText,0,0,1,1)
        qtMainLayout.addWidget(qtInput,1,0,1,1)
        qtMainLayout.addLayout(qtConfigLayout,0,1,2,1)
        
        
        
        qtText.setText("")
        
        self.qtInput = qtInput
        self.qtText = qtText
        self.qtHosts = qtHosts
        self.qtNetworkBox = qtNetworkBox
        self.qtNetworkTCP = qtNetworkTCP
        self.qtNetworkUDP = qtNetworkUDP
        self.qtHostsLayout = qtHostsLayout
        self.qtBroadcast = qtBroadcast
        
        def onReturn():
            msg = self.qtInput.text().strip()
            if(msg):
                self.onInput(msg)
            self.qtInput.setText("")
            
        qtInput.returnPressed.connect(onReturn)
        qtNetworkTCP.toggled.connect(onNetworkChange)
        qtNetworkUDP.toggled.connect(onNetworkChange)
        
        
        self.setupTcp()
        
        self.addHost("Node-A", ip="127.0.0.1")
        self.addHost("Node-B", ip="127.0.0.2")
        self.addHost("Node-C", ip="127.0.0.3")
        self.addHost("Node-D", ip="127.0.0.4")
        self.addHost("Node-E", ip="127.0.0.5")
        self.addHost("Node-F", ip="127.0.0.6")
    
    def setupTcp(self):
        self.chatTcp = ChatTcp('127.0.0.1', 5001)
        self.chatTcp.sig_receive.connect(lambda host, msg: self.tcpRecv(host, msg))
        
        self.chatTcp_thread = QThread()
        self.chatTcp_thread.setTerminationEnabled(False)
        
        self.chatTcp_thread.started.connect(self.chatTcp.started)
        self.chatTcp_thread.finished.connect(self.chatTcp_thread.deleteLater)        
        
        self.chatTcp.moveToThread(self.chatTcp_thread)
        
        self.chatTcp_thread.start()

        
    def tcpSend(self, host_data, msg):
        logging.info("tcpSend "+host_data['host'])
        self.chatTcp.loop.call_soon_threadsafe(self.chatTcp.send, host_data,msg)
        
        #self.sig_tcp_send.emit(host, msg)
        
        
    def tcpRecv(self, host, msg):
        self.addMessage(host, msg, nameColor=QColor(255,0,0))
        
    def setBroadcast(self, state):
        self.qtHosts.setEnabled(not state)
        if state:
            self.qtNetworkUDP.toggle()
        
    def addMessage(self, host, msg, nameColor=QColor(0,0,255)):
        self.qtText.moveCursor(QTextCursor.End)
        self.qtText.setTextColor(nameColor)
        self.qtText.insertPlainText("[{}] ".format(host))
        self.qtText.setTextColor(QColor(0,0,0))
        self.qtText.insertPlainText(msg)
        self.qtText.insertPlainText("\n")
        self.qtText.moveCursor(QTextCursor.End)
        
    def onInput(self, msg):
        
        self.addMessage("me", msg)
        
        if self.qtNetworkTCP.isChecked():
            for host, host_data in self.hosts.items():
                if host_data['checkbox'].checkState() == 2:
                    self.tcpSend(host_data, msg)
    
    def addHost(self, host, alias=None, ip=None):
        if not alias:
            alias=host
        
        checkbox = QCheckBox(alias)
        self.qtHostsLayout.addWidget(checkbox)
        
        self.hosts[host] = {
            'host': host,
            'alias': alias,
            'checkbox': checkbox,
            'ip': ip,
        }

