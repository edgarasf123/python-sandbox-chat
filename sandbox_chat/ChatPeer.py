import uuid as _uuid
import re

re_spaces = re.compile(r'[\s]+')
re_name_strip = re.compile(r'[^0-9a-zA-Z-_]+')

class ChatPeer():
    def __init__(self, uuid=None, host=None, udp_port=None, tcp_port=None, local=False):
        self.__uuid = uuid if uuid else _uuid.uuid4()
        self.host = host
        self.__name = None
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.local = local
        
    @property
    def uuid(self):
        return self.__uuid
        
    @property
    def udp_addr(self):
        return (self.host,self.udp_port)
        
    @property
    def tcp_addr(self):
        return (self.host,self.tcp_port)
    
    @property
    def name(self):
        if self.__name:
            return self.__name
        elif self.local:
            return "me"
        elif self.host:
            return self.host
        else:
            return str(self.uuid)
            
    
    @name.setter
    def name(self, name):
        global re_spaces
        global re_name_strip
        name = name [0:16] # Limit name length
        name = re_spaces.sub('_', name) # Replace spaces to underscore
        name = re_name_strip.sub('', name) # Remove unwanted characters
        
        if name == "me":
            name = ".me"
            
        self.__name = name
        
    def __del__(self):
        pass