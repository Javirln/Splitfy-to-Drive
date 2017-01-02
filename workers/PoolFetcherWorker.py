from PyQt5 import QtCore
from bs4 import BeautifulSoup


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
