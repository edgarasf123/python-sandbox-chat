
from PyQt5.QtCore import QObject

class Menu(QObject):
    def __init__(self, name):
        super().__init__()
        self.name = name
    
    def onClick(self):
        pass