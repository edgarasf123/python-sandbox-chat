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

class UdpProtocol(asyncio.Protocol):
    def __init__(self, master):
        self.master = master
        self.local_uuid = self.master.local_peer.uuid
        self.peers = self.master.peers
        self.loop = asyncio.get_event_loop()
        
    def connection_made(self, transport):
        self.transport = transport

    def error_received(self, err):
        logging.info(err)

    def datagram_received(self, data, addr):
        
        if len(data)<32:
            logging.info("Datagram packet too short! {}".format(len(data)))
            return
        try:
            uuid_from = uuid.UUID(bytes=data[0:16])
            uuid_to = uuid.UUID(bytes=data[16:32])
            
        except ValueError:
            pass
        
        # Check if we are the recipient
        if not uuid_to in (self.local_uuid, uuid_broadcast):
            return
        
        # Ignore our own packets
        if uuid_from == self.local_uuid:
            return
        
        if not uuid_from in self.peers:
            peer_from = ChatPeer(uuid=uuid_from, host=addr[0], udp_port=addr[1], tcp_port=5012)
        else:
            peer_from = self.peers[uuid_from]
        
        # Additional pointless checks for packet source
        if peer_from.udp_addr != addr:
            #logging.info("Ugh? {}!={}".format(peer_from.udp_addr, addr))
            pass #return
            
        logging.info("{} {}".format(str(addr), data))
        self.master.sig_peer_data.emit(peer_from, data[32:])
        
    
            
class ChatUdp(QObject):
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
        self.outbox = {}
        self.transport = None
        self.protocol = None
        self.aes_key = ""
    
    async def _main(self):
        logging.info("ChatUdp._main()")
        
        listen = self.loop.create_datagram_endpoint(
            lambda: UdpProtocol(self),
            local_addr=(self.ip, self.port),
            reuse_address=True,
            reuse_port=True,
            allow_broadcast=True
            )
        
        self.transport, self.protocol = await listen
        
        await self._announce_loop()
        
    @pyqtSlot()
    def started(self):
        logging.info("ChatUdp.started()")
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
        logging.info("ChatUdp.message()")
        self.loop.create_task(self._message(msg, peer))
    
    @pyqtSlot()
    def announce(self):
        logging.info("ChatUdp.announce()")
        self.loop.create_task(self._announce())
        
    @pyqtSlot(str)
    def update_aes(self, aes_key):
        logging.info("ChatUdp.update_aes()")
        self.aes_key = aes_key
    
    async def _announce_loop(self):
        while True:
            await self._announce()
            await asyncio.sleep(10)
    
    async def _announce(self):
        logging.info("ChatUdp._announce()")
        await self._send("ANNOUNCE {}".format("" if self.local_peer.name == "me" else self.local_peer.name ))
            
    async def _message(self, msg, peer=None):
        logging.info("ChatUdp._message()")
        await self._send("MSG {}".format(msg), peer)
    
    async def _message_encrypted(self, msg, peer=None):
        #cipher = AES.new(self.aes_key, AES.MODE_CBC)
        #ct_bytes = cipher.encrypt(pad(msg, AES.block_size))
        #iv = b64encode(cipher.iv).decode('utf-8')
        #ct = b64encode(ct_bytes).decode('utf-8')
        
        #await self._send("MSGE {} {}".format(iv,ct))
        pass
        
    async def _send(self, data, peer=None):
        logging.info("ChatUdp._send()")
        data_src = self.local_peer.uuid.bytes
        data_dst = peer.uuid.bytes if peer else uuid_broadcast.bytes
        data = data.encode() if isinstance(data,str) else data
        
        data_payload = data_src+data_dst+data
        
        if self.transport:
	        self.transport.sendto(data_payload, peer.udp_addr if peer else ('10.255.255.255', self.port))
