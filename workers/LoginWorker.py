from PyQt5 import QtCore


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