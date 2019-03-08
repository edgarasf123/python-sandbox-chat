from sandbox_chat import Menu


from PyQt5.QtWidgets import QTextBrowser

class MenuTraffic(Menu):
    def __init__(self):
        super().__init__("Traffic")
        self.widget = QTextBrowser()
        self.widget.setText("Traffic")