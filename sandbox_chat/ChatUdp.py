from asyncio import Queue
from threading import Thread
from socket import socket

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject

import sys
import asyncio


class UdpHost(asyncio.Protocol):
    def __init__(self, host=None, master=None):
        
        if host:
            self.host = host
            self.master.peers[self.host] = self
        
        self.master = master
        self.msgQueue = Queue()
        self.firstPacket = True
        
        self._ready = asyncio.Event()
        loop = asyncio.get_event_loop()
        asyncio.create_task(self._check_queue())
        
    def data_received(self, data):
        msg = data.decode().strip()
        if self.firstPacket:
            new_host = msg
            self.firstPacket = False
        elif msg:
            self.master.sig_message.emit(self.host, msg)
        
    def connection_made(self, transport):
        self.host = transport.get_extra_info('peername')
        self.host = '{}:{}'.format(*self.host)
        self.transport = transport
        
        self.master.peers[self.host] = self
        self.transport.write(self.master.host.encode() + b'\n')
        
        print("{} connected".format(self.host))
        self._ready.set()
        

    def connection_lost(self, exc):
        print("{} disconnected".format(self.host))
        del self.master.peers[self.host]

        
    async def _check_queue(self):
        await self._ready.wait()
        while True:
            msg = await self.msgQueue.get()
            self.transport.write(msg.encode()+b'\n')
            
            
class ChatUdp(QObject):
    sig_message = pyqtSignal(str, str)
    sig_connect = pyqtSignal(str)
    sig_diconnect = pyqtSignal(str)
    
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.peers = {}
        
    
    async def main(self):
        loop = asyncio.get_event_loop()
        self.loop = loop
        # Each client will create a new protocol instance
        srv = await loop.create_server(lambda: TcpHost(master=self), '0.0.0.0', self.port)
        
        async with srv:
            print('Serving on {}'.format(srv.sockets[0].getsockname()))
            await srv.serve_forever()
        
        print('Done serving')
        
    @pyqtSlot()
    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        asyncio.run(self.main(), debug=True)
        
    @pyqtSlot(str, str)
    def message(self, host, msg):
        asyncio.run_coroutine_threadsafe(self.__assync__message(host,msg), loop=self.loop)
                
    @pyqtSlot(str)
    def broadcast(self, msg):
        asyncio.run_coroutine_threadsafe(self.__assync__broadcast(msg), loop=self.loop)
        
    async def __assync__message(self, host, msg):
        await self.peers[host].msgQueue.put(msg)
        
    
    async def __assync__broadcast(self, msg):
        for x in self.peers.values():
            await x.msgQueue.put(msg)
        
    async def connect(self, host):
        transport, protocol = await loop.create_connection(
        lambda: TcpHost(message, on_con_lost, loop),
        '127.0.0.1', 8888)