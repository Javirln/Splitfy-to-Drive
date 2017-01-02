import re

import requests
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from bs4 import BeautifulSoup


class MainProcess(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi("splitfy-core.ui", self)
        self.openPools = {}
        self.s = requests.session()
        self.pushButtonSend.clicked.connect(self.send_form)

    def send_form(self):
        auth = {
            'UserLogin[username]': self.usernameLineEdit.text(),
            'UserLogin[password]': self.passwordLineEdit.text()

        }
        self.s.post('https://www.splitfy.com/login', data=auth)

        main_page = self.s.get('https://www.splitfy.com/profile')
        organized_events = BeautifulSoup(main_page.text, "lxml").findAll('div', attrs={'id': 'managerEvents'})

        for child in organized_events:
            child_tag = child.findAll('a', attrs={'href': re.compile("/bote/*")})
            for tag in child_tag:
                self.openPools[tag.text] = 'https://www.splitfy.com' + tag['href'].replace('/bote/p',
                                                                                           '/bote/p/aportaciones')
                self.comboBoxSplitfy.addItem(tag.text)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_process = MainProcess()
    main_process.show()
    sys.exit(app.exec_())
