from asyncio import Queue
from threading import Thread
from socket import socket
import threading
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject

import sys
import asyncio
import logging

    
class TcpPeerConnection(asyncio.Protocol):
    def __init__(self, master, peer):
        self.master = None
        self.peer = None
        
        self.first_packet = True
        
    def __del__(self):
        pass
        
    def data_received(self, data):
        self.master.sig_peer_data.emit(self.peer, data)
        
    def connection_made(self, transport):
        self.host = transport.get_extra_info('peername')
        
    def connection_lost(self, exc):
        pass
            
class ChatTcp(QObject):
    sig_received = pyqtSignal(str, str)
    sig_connect = pyqtSignal(str)
    sig_diconnect = pyqtSignal(str)
    
    def __init__(self, ip, port, name=""):
        super().__init__()
        
        self.name = name
        self.ip = ip
        self.port = port
        self.peers = set()
        self.outbox = {}
    
    async def main(self):
        logging.info("ChatTcp.main()".format(threading.get_ident()))
        
        #Each client will create a new protocol instance
        srv = await self.loop.create_server(lambda: TcpPeerConnection(self), self.ip, self.port)
        
        async with srv:
            await srv.serve_forever()

        
    @pyqtSlot()
    def started(self):
        
        
        logging.info("ChatTcp.started()")
        try: 
            self.loop = asyncio.new_event_loop()
            self.loop.set_debug(True)
            asyncio.set_event_loop(self.loop)
            
        
            self.new_client_lock = asyncio.Lock()
            
            logging.info(str(asyncio.get_event_loop()))
            self.loop.create_task(self.main())
            self.loop.run_forever()
        except: 
            (type, value, traceback) = sys.exc_info()
            sys.excepthook(type, value, traceback)
            
        
    @pyqtSlot(dict, str)
    def send(self, host_data, msg):
        logging.info("ChatTcp.send()")
        self.loop.create_task(self.__assync__message(host_data,msg))
        
                
    @pyqtSlot(str)
    def broadcast(self, msg):
        logging.info("ChatTcp.broadcast()")
        
        self.loop.create_task(self.__assync__broadcast(msg)).result()
    
    def peer_aliases(self, peer_data, existing=False):
        if isinstance(peer_data, TcpPeer):
            yield from self.peer_aliases(peer_data.data, existing)
            return
            
        if existing:
            for alias in self.peer_aliases(peer_data):
                if alias in self.peers:
                    yield alias
            return
        
        
        if isinstance(peer_data, str):
            yield peer_data
        elif isinstance(peer_data, dict):
            if 'alias' in peer_data:
                yield peer_data['alias']
            elif 'ip' in peer_data and 'port' in peer_data:
                yield '{}:{}'.format(peer_data['ip'],peer_data['port'])
        elif isinstance(peer_data, tuple) and len(peer_data) == 2 and isinstance(peer_data[0],str) and isinstance(peer_data[1],int):
            yield '{}:{}'.format(peer_data[0],peer_data[1])
    
    
    def find_peer(self, hint):
        for peer in self.peers:
            if peer.check_hint(hint):
                return peer
        return None
        
    def get_peer(self, host_data):
        peer = self.find_peer( host_data)
        if peer:
            return peer
        else:
            peer = TcpPeer(host_data, self)
            
            return peer
    
    async def __assync__message(self, host_data, msg):
        logging.info("ChatTcp.__assync__message()")
        peer = self.get_peer(host_data)
        
        await peer.outbox.put(msg)
    
    async def __assync__broadcast(self, msg):
        for x in self.outbox.values():
            await x.put(msg)

##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################
from asyncio import Queue
from threading import Thread
from socket import *
import threading
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject
from sandbox_chat import ChatPeer

from base64 import b64encode
#from Crypto.Cipher import AES
#from Crypto.Util.Padding import pad

import sys
import asyncio
import logging
import uuid

uuid_broadcast = uuid.UUID("{89a59843-5611-4d5a-a0ce-edcc8ac15f9e}")

class TcpProtocol(asyncio.Protocol):
    def __init__(self, master):
        self.master = master
        self.loop = asyncio.get_event_loop()
        self.peer = None
        
    def connection_lost(self, exc):
        pass
        
    def connection_made(self, transport):
        self.transport = transport
        transport.write(self.master.local_peer.uuid.bytes)
        
    def data_received(self, data):
        if not self.peer:
            peer_uuid = uuid.UUID(bytes=data)
            if peer_uuid in self.master.connections:
                transport.close()
                return
                
            self.peer = self.master.peers[peer_uuid]
            self.connections[peer_uuid] = self.transport
        else:
            self.master.sig_peer_data.emit(self.peer, data)
            
    
            
class ChatTcp(QObject):
    sig_connected = pyqtSignal(str, str)
    sig_received = pyqtSignal(ChatPeer, str)
    sig_diconnect = pyqtSignal(str)
    sig_peer_new = pyqtSignal(ChatPeer)
    sig_peer_name = pyqtSignal(ChatPeer, str)
    sig_peer_data = pyqtSignal(ChatPeer, bytes)
    
    def __init__(self, addr, peers, local_peer):
        super().__init__()
        
        self.addr = addr
        self.ip = addr[0]
        self.port = addr[1]
        self.peers = peers
        self.local_peer = local_peer
        self.connections = {}
        self.outbox = {}
        self.transport = None
        self.protocol = None
        self.aes_key = ""
    
    async def _main(self):
        logging.info("ChatTcp.main()")
        
        #Each client will create a new protocol instance
        srv = await self.loop.create_server(lambda: TcpProtocol(self), self.ip, self.port)
        
        async with srv:
            await srv.serve_forever()
        
    @pyqtSlot()
    def started(self):
        logging.info("ChatTcp.started()")
        try: 
            self.loop = asyncio.new_event_loop()
            self.loop.set_debug(True)
            asyncio.set_event_loop(self.loop)
            
        
            self.new_client_lock = asyncio.Lock()
            
            logging.info(str(asyncio.get_event_loop()))
            self.loop.create_task(self._main())
            self.loop.run_forever()
        except: 
            (type, value, traceback) = sys.exc_info()
            sys.excepthook(type, value, traceback)
            
        
    @pyqtSlot(dict, str, str)
    def message(self, msg, peer=None, aes=None):
        logging.info("ChatTcp.message()")
        self.loop.create_task(self._message(msg, peer))
    
    @pyqtSlot()
    def announce(self):
        logging.info("ChatTcp.announce()")
        self.loop.create_task(self._announce())
        
    @pyqtSlot(str)
    def update_aes(self, aes_key):
        logging.info("ChatTcp.update_aes()")
        self.aes_key = aes_key
    
    async def _announce_loop(self):
        while True:
            await self._announce()
            await asyncio.sleep(10)
    
    async def _announce(self):
        logging.info("ChatTcp._announce()")
        await self._send("ANNOUNCE {}".format("" if self.local_peer.name == "me" else self.local_peer.name ))
            
    async def _message(self, msg, peer=None):
        logging.info("ChatTcp._message()")
        await self._send("MSG {}".format(msg), peer)
    
    async def _message_encrypted(self, msg, peer=None):
        #cipher = AES.new(self.aes_key, AES.MODE_CBC)
        #ct_bytes = cipher.encrypt(pad(msg, AES.block_size))
        #iv = b64encode(cipher.iv).decode('utf-8')
        #ct = b64encode(ct_bytes).decode('utf-8')
        
        #await self._send("MSGE {} {}".format(iv,ct))
        pass
        
    async def _send(self, data, peer=None):
        logging.info("ChatTcp._send()")
        data_src = self.local_peer.uuid.bytes
        data_dst = peer.uuid.bytes if peer else uuid_broadcast.bytes
        data = data.encode() if isinstance(data,str) else data
        
        data_payload = data_src+data_dst+data
        
        
        self.transport.sendto(data_payload, peer.udp_addr if peer else ('255.255.255.255', self.port))
        