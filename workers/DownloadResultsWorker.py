import re
from PyQt5 import QtCore


class DownloadResultsWorker(QtCore.QThread):
    data_sent = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(DownloadResultsWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self._session = None
        self._from_url = ""
        self._filename = ""

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        pool_results = self._session.get(
            'https://www.splitfy.com/evento/downloadCollaboratorsCSV/id/' + re.search('[0-9]+', self._from_url).group(
                0))
        if self._filename != "":
            with open(self._filename + ".csv", 'w') as file:
                file.write(pool_results.text)
                file.close()
            self.data_sent.emit("Archivo descargado")
        else:
            self.data_sent.emit("El nombre del archivo no puede estar en blanco")

    def set_from_url(self, from_url):
        self._from_url = from_url

    def set_session(self, session):
        self._session = session

    def set_filename(self, filename):
        self._filename = filename
