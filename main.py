import re

import requests
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from bs4 import BeautifulSoup


class MainProcess(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi("splitfy-core.ui", self)
        self.open_pools = {}
        self.session = requests.session()

        self._login_worker = LoginWorker()
        self._login_worker.data_sent.connect(self.login_worker_callback)

        self._pools_worker = PoolsWorker()
        self._pools_worker.data_sent.connect(self.pools_worker_callback)

        self._pool_fetcher_worker = PoolFetcherWorker()
        self._pool_fetcher_worker.data_sent.connect(self.pool_fetcher_worker_callback)
        self.connections()

    def connections(self):
        self.pushButtonSend.clicked.connect(self.handle_login)
        self.comboBoxSplitfy.activated[str].connect(self.handle_pool_fetcher)

    def login_worker_callback(self, session):
        self.session = session

        if self._pools_worker.isRunning():
            self._pools_worker.stop()
        else:
            self._pools_worker.set_session(self.session)
            self._pools_worker.start()

    def pools_worker_callback(self, pools):
        self.open_pools = dict(pools)
        self.comboBoxSplitfy.addItems(pools)

    def pool_fetcher_worker_callback(self, pool_info):
        self.labelBoteValue.setText(pool_info["pool_name"])
        self.labelBoteValue.adjustSize()

        self.labelRecaudadoValue.setText(str(pool_info["money_total_amount"]) + '€')
        self.labelPersonasValue.setText(str(pool_info["people_total_amount"]))

    def send_form(self):
        auth = {
            'UserLogin[username]': self.usernameLineEdit.text(),
            'UserLogin[password]': self.passwordLineEdit.text()

        }
        self.session.post('https://www.splitfy.com/login', data=auth)

        main_page = self.session.get('https://www.splitfy.com/profile')
        organized_events = BeautifulSoup(main_page.text, "lxml").findAll('div', attrs={'id': 'managerEvents'})

        for child in organized_events:
            child_tag = child.findAll('a', attrs={'href': re.compile("/bote/*")})
            for tag in child_tag:
                self.open_pools[tag.text] = 'https://www.splitfy.com' + tag['href'].replace('/bote/p',
                                                                                            '/bote/p/aportaciones')
                self.comboBoxSplitfy.addItem(tag.text)

    def update_statistics(self, text):
        self.labelBoteValue.setText(text)
        self.labelBoteValue.adjustSize()

        pool_info = self.session.get(self.open_pools.get(text))

        soup = BeautifulSoup(pool_info.text, "lxml")

        names = soup.findAll('td', attrs={'class': ''})
        prices = soup.findAll('td', attrs={'style': 'font-weight:bolder;'})

        money_total_amount = sum([float(price.text) for price in prices])
        people_total_amount = len(names)

        self.labelRecaudadoValue.setText(str(money_total_amount) + '€')
        self.labelPersonasValue.setText(str(people_total_amount))

    def handle_login(self):
        if self._login_worker.isRunning():
            self._login_worker.stop()
        else:
            self._login_worker.set_username(self.usernameLineEdit.text())
            self._login_worker.set_password(self.passwordLineEdit.text())
            self._login_worker.set_session(self.session)

            self._login_worker.start()

    def handle_pool_fetcher(self, pool_to_search):
        if self._pool_fetcher_worker.isRunning():
            self._pools_worker.stop()
        else:
            self._pool_fetcher_worker.set_session(self.session)
            self._pool_fetcher_worker.set_open_pools(self.open_pools)
            self._pool_fetcher_worker.set_pool_to_search(pool_to_search)

            self._pool_fetcher_worker.start()


class LoginWorker(QtCore.QThread):
    data_sent = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(LoginWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self._username = ""
        self._password = ""
        self._session = None

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False
        auth = {
            'UserLogin[username]': self._username,
            'UserLogin[password]': self._password

        }
        self._session.post('https://www.splitfy.com/login', data=auth)

        self.data_sent.emit(self._session)

    def set_username(self, username):
        self._username = username

    def set_password(self, password):
        self._password = password

    def set_session(self, session):
        self._session = session


class PoolsWorker(QtCore.QThread):
    data_sent = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(PoolsWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self._local_pools = {}
        self._session = None

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        main_page = self._session.get('https://www.splitfy.com/profile')
        organized_events = BeautifulSoup(main_page.text, "lxml").findAll('div', attrs={'id': 'managerEvents'})

        for child in organized_events:
            child_tag = child.findAll('a', attrs={'href': re.compile("/bote/*")})
            for tag in child_tag:
                self._local_pools[tag.text] = 'https://www.splitfy.com' + tag['href'].replace('/bote/p',
                                                                                              '/bote/p/aportaciones')

        self.data_sent.emit(self._local_pools)

    def set_session(self, session):
        self._session = session


class PoolFetcherWorker(QtCore.QThread):
    data_sent = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super(PoolFetcherWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self._session = None
        self._pool_to_search = ""
        self._open_pools = {}

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        pool_info = self._session.get(self._open_pools.get(self._pool_to_search))

        soup = BeautifulSoup(pool_info.text, "lxml")

        names = soup.findAll('td', attrs={'class': ''})
        prices = soup.findAll('td', attrs={'style': 'font-weight:bolder;'})

        money_total_amount = sum([float(price.text) for price in prices])
        people_total_amount = len(names)

        self.data_sent.emit({"pool_name": self._pool_to_search,
                             "money_total_amount": money_total_amount,
                             "people_total_amount": people_total_amount})

    def set_session(self, session):
        self._session = session

    def set_pool_to_search(self, pool_to_search):
        self._pool_to_search = pool_to_search

    def set_open_pools(self, open_pools):
        self._open_pools = open_pools


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_process = MainProcess()
    main_process.show()
    sys.exit(app.exec_())
