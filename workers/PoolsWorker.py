import re
from PyQt5 import QtCore
from bs4 import BeautifulSoup


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
