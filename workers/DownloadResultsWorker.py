import re

from PyQt5 import QtCore


class DownloadResultsWorker(QtCore.QThread):
    send_message = QtCore.pyqtSignal(str)
    data_send = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(DownloadResultsWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self.__session = None
        self.__from_url = ""
        self.__filename = ""
        self.__is_to_google = False
        self.__pool_results = None

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        self.__pool_results = self.__session.get(
            'https://www.splitfy.com/evento/downloadCollaboratorsCSV/id/' + re.search('[0-9]+', self.__from_url).group(
                0))
        if self.__is_to_google:
            self.data_send.emit(self.__pool_results.text)
        else:
            if self.__filename != "":
                with open(self.__filename + ".csv", 'w') as file:
                    file.write(self.__pool_results.text)
                    file.close()
                self.__pool_results = None
                self.send_message.emit("Archivo descargado")
            else:
                self.send_message.emit("El nombre del archivo no puede estar en blanco")

    def set_from_url(self, from_url):
        self.__from_url = from_url

    def set_session(self, session):
        self.__session = session

    def set_filename(self, filename):
        self.__filename = filename

    def set_is_to_googe(self, is_to_google):
        self.__is_to_google = is_to_google
