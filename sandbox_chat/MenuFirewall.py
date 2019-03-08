from sandbox_chat import Menu
from PyQt5.QtWidgets import QTextBrowser

class MenuFirewall(Menu):
    def __init__(self):
        super().__init__("Firewall")
        self.widget = QTextBrowser()
        self.widget.setText("Firewall widget")