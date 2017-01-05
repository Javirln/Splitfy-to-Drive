from PyQt5 import QtCore


class LoginWorker(QtCore.QThread):
    data_sent = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(LoginWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self.__username = ""
        self.__password = ""
        self.__session = None

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False
        auth = {
            'UserLogin[username]': self.__username,
            'UserLogin[password]': self.__password

        }
        self.__session.post('https://www.splitfy.com/login', data=auth)

        self.data_sent.emit(self.__session)

    def set_username(self, username):
        self.__username = username

    def set_password(self, password):
        self.__password = password

    def set_session(self, session):
        self.__session = session
