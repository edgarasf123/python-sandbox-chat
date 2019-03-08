from sandbox_chat import Menu, ChatTcp, ChatUdp, ChatPeer
from PyQt5.QtWidgets import QWidget, QGridLayout, QTextBrowser, QLineEdit, QVBoxLayout, QHBoxLayout, QGroupBox, QCheckBox, QRadioButton, QLineEdit, QLabel, QSizePolicy
from PyQt5.QtGui import QColor, QTextCursor 
from PyQt5.QtCore import QThread, QSize
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject
#from Crypto.Cipher import AES


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
        
        qtPeers = QGroupBox("Recipients")
        qtPeersLayout = QVBoxLayout(qtPeers)
        
        
        def onBroadcastChange(state):
            self.setBroadcast(state>0)
            
        qtBroadcast = QCheckBox("Broadcast")
        qtBroadcast.stateChanged.connect(onBroadcastChange)
        
        
        qtNetworkBox = QGroupBox("Network")
        qtNetworkLayout = QVBoxLayout(qtNetworkBox)

        def onNetworkChange():
            if self.qtNetworkTcp.isChecked():
                self.qtPeers.setEnabled(True)
                
                self.qtBroadcast.setEnabled(False)
                self.qtBroadcast.setCheckState(0)
            elif self.qtNetworkUdp.isChecked():
                self.qtBroadcast.setEnabled(True)
                
            
        qtNetworkTcp = QRadioButton("TCP")
        qtNetworkUdp = QRadioButton("UDP")
        qtNetworkBox.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,QSizePolicy.Maximum))

        qtNetworkLayout.addWidget(qtNetworkTcp)
        qtNetworkLayout.addWidget(qtNetworkUdp)
        
        qtNetworkUdp.toggle()
        
        qtConfigLayout.addWidget(qtBroadcast)
        qtConfigLayout.addWidget(qtPeers)
        qtConfigLayout.addWidget(qtNetworkBox)
        
        qtMainLayout.addWidget(qtText,0,0,1,1)
        qtMainLayout.addWidget(qtInput,1,0,1,1)
        qtMainLayout.addLayout(qtConfigLayout,0,1,2,1)
        
        qtText.setText("")
        
        qtSettingsLayout = QGridLayout()
        
        qtNameLabel = QLabel("Name")
        qtName = QLineEdit()
        qtNameLabel.setMaximumWidth(40)
        qtName.setMaximumWidth(100)
        
        qtAesLabel = QLabel("AES")
        qtAes = QLineEdit()
        qtAesLabel.setMaximumWidth(40)
        qtAes.setMaximumWidth(100)
        
        qtSettingsLayout.addWidget(qtNameLabel,0,0,1,1)
        qtSettingsLayout.addWidget(qtName,0,1,1,1)
        #qtSettingsLayout.addWidget(qtAesLabel,1,0,1,1)
        #qtSettingsLayout.addWidget(qtAes,1,1,1,1)
        
        qtConfigLayout.addLayout(qtSettingsLayout)
        
        self.qtInput = qtInput
        self.qtText = qtText
        self.qtPeers = qtPeers
        self.qtNetworkBox = qtNetworkBox
        self.qtNetworkTcp = qtNetworkTcp
        self.qtNetworkUdp = qtNetworkUdp
        self.qtPeersLayout = qtPeersLayout
        self.qtBroadcast = qtBroadcast
        self.qtName = qtName
        
        def onReturn():
            msg = self.qtInput.text().strip()
            if(msg):
                self.onInput(msg)
            self.qtInput.setText("")
            
        qtInput.returnPressed.connect(onReturn)
        qtNetworkTcp.toggled.connect(onNetworkChange)
        qtNetworkUdp.toggled.connect(onNetworkChange)
        
        def aes_update():
            self.aes_key = self.qtAes.text()
            self.chatUdp.loop.call_soon_threadsafe(self.chatUdp.update_aes, self.aes_key)
            
        
        qtName.editingFinished.connect(lambda: self.setName(self.qtName.text().strip()))
        qtAes.editingFinished.connect(aes_update)
        
        
        qtBroadcast.setCheckState(2)
        
        self.local_peer = ChatPeer(local=True)
        self.peers = {}
        self.peers_checkboxes = {}
        self.peers[self.local_peer.uuid] = self.local_peer
        self.aes_key = ""
        
        self.setupTcp()
        self.setupUdp()


        qtName.setText(socket.gethostname())
        self.local_peer.name = socket.gethostname()
    
    def setupTcp(self):
        self.chatTcp = ChatUdp(('0.0.0.0', 5002), peers=self.peers, local_peer=self.local_peer)
        self.chatTcp.sig_peer_data.connect(lambda peer, data: self.peer_data(peer, data))  
        
        self.chatTcp_thread = QThread()
        self.chatTcp_thread.setTerminationEnabled(False)
        
        self.chatTcp_thread.started.connect(self.chatTcp.started)
        self.chatTcp_thread.finished.connect(self.chatTcp_thread.deleteLater)      
        
        self.chatTcp.moveToThread(self.chatTcp_thread)
        
        self.chatTcp_thread.start()

        
    def tcpSend(self, host_data, msg):
        logging.info("tcpSend "+host_data['host'])
        self.chatTcp.loop.call_soon_threadsafe(self.chatTcp.send, host_data,msg)    
        
    def setupUdp(self):
        self.chatUdp = ChatUdp(('0.0.0.0', 5001), peers=self.peers, local_peer=self.local_peer)
        #self.chatUdp.sig_received.connect(lambda peer, msg: self.encryptedMessage(peer, msg))
        self.chatUdp.sig_peer_new.connect(lambda peer: self.peer_new(peer))
        self.chatUdp.sig_peer_name.connect(lambda peer, name: self.peer_name(peer, name))
        self.chatUdp.sig_peer_data.connect(lambda peer, data: self.peer_data(peer, data))
        
        self.chatUdp_thread = QThread()
        self.chatUdp_thread.setTerminationEnabled(False)
        
        self.chatUdp_thread.started.connect(self.chatUdp.started)
        self.chatUdp_thread.finished.connect(self.chatUdp_thread.deleteLater)        
        
        self.chatUdp.moveToThread(self.chatUdp_thread)
        
        self.chatUdp_thread.start()

        
    def udpSend(self, msg, peer=None):
        logging.info("udpSend() ")
        self.chatUdp.loop.call_soon_threadsafe(self.chatUdp.message, msg, peer)
        
    
    def setBroadcast(self, state):
        self.qtPeers.setEnabled(not state)
        if state:
            self.qtNetworkUdp.toggle()
        
    def addMessage(self, peer, msg):
        self.qtText.moveCursor(QTextCursor.End)
        self.qtText.setTextColor(QColor(0,0,255) if peer == self.local_peer else QColor(255,0,0))
        self.qtText.insertPlainText("[{}] ".format(peer.name))
        self.qtText.setTextColor(QColor(0,0,0))
        self.qtText.insertPlainText(msg)
        self.qtText.insertPlainText("\n")
        self.qtText.moveCursor(QTextCursor.End)
        
    def encrytedMessage(self, peer, msg):
        self.addMessage(peer, msg)
    
    
    def onInput(self, msg):
        
        self.addMessage(self.local_peer, msg)
        
        if self.qtNetworkTcp.isChecked():
            for uuid, peers in self.peers.items():
                if uuid in self.peers_checkboxes and self.peers_checkboxes[uuid].checkState() == 2:
                    self.tcpSend(peer, msg)
        elif self.qtNetworkUdp.isChecked():
            if self.qtBroadcast.checkState() == 2:
                self.udpSend(msg)
            else:
                for uuid, peer in self.peers.items():
                    if uuid in self.peers_checkboxes and self.peers_checkboxes[uuid].checkState() == 2:
                        self.udpSend(msg, peer)
                        
    def setName(self, name):
        logging.info("New name: {}".format(name))
        self.local_peer.name = name
        self.chatUdp.loop.call_soon_threadsafe(self.chatUdp.announce) 
        
        
        
    def addHost(self, host, alias=None, ip=None):
        if not alias:
            alias=host
        
        
        self.hosts[host] = {
            'host': host,
            'alias': alias,
            'checkbox': checkbox,
            'ip': ip,
        }
    
    def peer_new( self, peer ):
        
        checkbox = QCheckBox(peer.name)
        self.qtPeersLayout.addWidget(checkbox)
        self.peers[peer.uuid] = peer
        self.peers_checkboxes[peer.uuid] = checkbox
        
    def peer_name_changed(self, peer):
        self.peers_checkboxes[peer.uuid].setText(peer.name)

    def peer_data(self, peer, data):
        cmd, *opts = data.decode().split(' ',1)
        cmd = cmd.upper()
        opts = opts[0] if opts else None
        
            
        def CMD_MSG(opts):
            self.addMessage(peer, opts)
        
        def CMD_ANNOUNCE(opts):
            if opts:
                old_name = peer.name
                peer.name = opts
                if old_name != peer.name:
                    self.peer_name_changed(peer)
        
        commands = {
            'MSG': CMD_MSG,
            'ANNOUNCE': CMD_ANNOUNCE,
        }
        
        if cmd in commands:
            commands[cmd](opts)