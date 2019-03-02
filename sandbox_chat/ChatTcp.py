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
    def __init__(self, peer):
        self.peer = None
        self.master = None
        
        if isinstance(peer, ChatTcp):
            self.master = peer
        else:
            self.master = peer.master
        
        self.host = ()
        self.first_packet = True
        
    def __del__(self):
        pass
        
    def data_received(self, data):
        msg = data.decode().strip()
        if self.first_packet:
            if not self.peer:
                peer_data = {
                    'alias': '{}:{}'.format(*self.host),
                    'ip': self.host[0]
                }
                peer = TcpPeer(peer_data, self.master)
                self.peer = peer
            
            if msg:
                self.peer.name = msg
            else:
                self.peer.name = '{}:{}'.format(*self.host)
                
            self.first_packet = False
                
            
        elif msg:
            self.peer._inbox(msg)
            
    def connection_made(self, transport):
        transport.write(self.master.name.encode() + b'\n')
        self.host = transport.get_extra_info('peername')
        
    def connection_lost(self, exc):
        pass
            

class TcpPeer():
    def __init__(self, data, master, loop=None):
        self.master = master
        self.data = data
        self.loop = loop if loop else asyncio.get_event_loop()
        self.name = data['alias'] if 'alias' in data else None
        self.lock = asyncio.Lock()
        self.outbox = Queue()
        self.transport = None
        self.protocol = None
        
        self.name = data['alias'] if 'alias' in data else None
        
        self.loop.create_task(self._outbox_worker())
        
        master.peers.add(self)

        logging.info('Peer {}: created'.format(self.name))
        
    async def update(self):
        logging.info('Peer {}: updating'.format(self.name))
        # Update aliases
        pass
        
    async def _get_connection(self):
        while not self.transport or self.transport.is_closing():
            logging.info('Peer {}: initiating a link'.format(self.name))
            try:
                self.transport, self.protocol = await self.loop.create_connection(lambda: TcpPeerConnection(self), host=self.data['ip'], port=self.master.port)
                break
            except TimeoutError:
                pass
            except ConnectionRefusedError:
                pass
        return self.transport
    def _inbox(self, msg):
        logging.info('Peer {}: message - {}'.format(self.name, msg))
        self.master.sig_receive.emit(self.name, msg)
            
    async def _outbox_worker(self):
        while True:
            msg = await self.outbox.get()
            
            await self._get_connection()
            
            self.transport.write(msg.encode()+b'\n')
            
            
    def aliases(self, existing=False, missing=False, invalid=False):
        if existing:
            for alias in self.aliases(peer_data):
                if existing and alias in self.master.peers:
                    yield alias
                elif missing and not alias in self.master.peers:
                    yield alias
            return
        
        if invalid:
            valid_aliases = list(self.aliases(peer_data))
            for alias, peer in self.peers.items():
                if peer is self and not alias in valid_aliases:
                    yield alias
                    
        if self.name:
            yield self.name
        
        if 'alias' in self.data:
            yield self.data['alias']
        
        if 'ip' in self.data and 'port' in self.data:
            yield '{}:{}'.format(self.data['ip'],self.data['port'])
        
    def check_hint(self, hint):
        if 'alias' in self.data and isinstance(hint, dict) and 'alias' in hint:
            return hint['alias'] == self.data['alias']
        elif isinstance(hint, tuple):
            return self.transport.get_extra_info('peername') == hint
        #    yield '{}:{}'.format(peer_data[0],peer_data[1])
        return False
    
        
    
            
class ChatTcp(QObject):
    sig_receive = pyqtSignal(str, str)
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
        