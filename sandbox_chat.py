#!/usr/bin/python3

import os
#os.environ["QT_QPA_PLATFORM"] = "linuxfb"
#os.environ["QT_QPA_GENERIC_PLUGINS"] = "evdevmouse"
#os.environ["QT_QPA_EVDEV_MOUSE_PARAMETERS"] = "/dev/input/event0"
#os.environ["QT_QPA_FB_HIDECURSOR"] = "0"
#os.environ["QT_SCALE_FACTOR"] = "2"

import sys

import threading
import logging

from sandbox_chat import Menu
from sandbox_chat import MenuChat
from sandbox_chat import MenuTraffic
from sandbox_chat import MenuFirewall

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout, QSizePolicy, QStackedWidget, QTextBrowser, QLineEdit, QCheckBox, QRadioButton 
from PyQt5.QtGui import QIcon, QColor, QTextCursor 
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSlot
 
    
    
class MenuExit(Menu):
    def __init__(self):
        super().__init__("Quit")
        self.widget = QWidget()
        
    def onClick(self):
        sys.exit()
        

      
class App(QDialog):
    def __init__(self):
        super().__init__()
        self.left = 10
        self.top = 10
        self.width = 800
        self.height = 600
        self.initUI()
     
    def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
         
         
         
        self.createSidebar()
        self.createContent()
         
        self.windowLayout = QHBoxLayout(self)
        self.windowLayout.addWidget(self.sidebar)
        self.windowLayout.addWidget(self.content)
        
        self.addMenu(MenuChat())
        self.addMenu(MenuTraffic())
        self.addMenu(MenuFirewall())
        self.addMenu(MenuExit())
        
        self.content.setCurrentIndex(0)
    
        self.show()
        
    def addMenu(self, menu):
        menuButton = QPushButton(menu.name)
        menuButton.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum))
                
        self.sidebarLayout.addWidget(menuButton)
        contentIndex = self.content.addWidget(menu.widget)
        
        def onClick():
            self.content.setCurrentIndex(contentIndex)
            menu.onClick()
            
        menuButton.clicked.connect(onClick)

        
    def createSidebar(self):
        self.menuStack = QStackedWidget()
        
        sidebar = QWidget()
        sidebarLayout = QVBoxLayout()
        sidebar.setLayout( sidebarLayout )
        
        sidebar.setSizePolicy(QSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum))
        
        #layout.setColumnStretch(1, 4)
        #layout.setColumnStretch(2, 4)
        
        self.sidebarLayout = sidebarLayout
        self.sidebar = sidebar
        
    def createContent(self):
        self.content = QStackedWidget()
        self.content.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding))

if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG, format='%(relativeCreated)6d %(threadName)s %(message)s')
    print("main() thread",threading.get_ident())
        
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())