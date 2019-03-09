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
        logging.info(data)
        if not self.peer:
            logging.info("New connetion------------------")
            
            peer_uuid = uuid.UUID(bytes=data[0:16])
            if peer_uuid in self.master.connections:
                self.transport.close()
                logging.info("Duplicate connection")
                return
                
            self.peer = self.master.peers[peer_uuid]
            self.master.connections[peer_uuid] = self.transport
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
        
        #async with srv:
        #    await srv.serve_forever()
        
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
            
    async def _message(self, msg, peer):
        logging.info("ChatTcp._message()")
        await self._send("MSG {}".format(msg), peer)
    
    async def _message_encrypted(self, msg, peer):
        #cipher = AES.new(self.aes_key, AES.MODE_CBC)
        #ct_bytes = cipher.encrypt(pad(msg, AES.block_size))
        #iv = b64encode(cipher.iv).decode('utf-8')
        #ct = b64encode(ct_bytes).decode('utf-8')
        
        #await self._send("MSGE {} {}".format(iv,ct))
        pass
        
    async def _send(self, data, peer):
        logging.info("ChatTcp._send()")
        data_src = self.local_peer.uuid.bytes
        data_dst = peer.uuid.bytes if peer else uuid_broadcast.bytes
        data = data.encode() if isinstance(data,str) else data
        
        data_payload = data #data_src+data_dst+data
        
        if not peer.uuid in self.connections:
            transport, protocol = await self.loop.create_connection(lambda: TcpProtocol(self), peer.tcp_addr[0], peer.tcp_addr[1])
        

        if peer.uuid in self.connections:
            self.connections[peer.uuid].write(data_payload)
        
