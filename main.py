import requests
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMainWindow

from workers.DownloadResultsWorker import DownloadResultsWorker
from workers.GoogleWorker import GoogleWorker
from workers.LoginWorker import LoginWorker
from workers.PoolFetcherWorker import PoolFetcherWorker
from workers.PoolsWorker import PoolsWorker


class MainProcess(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi("splitfy-core.ui", self)
        self.open_pools = {}
        self.google_files = None
        self.session = requests.session()

        self._login_worker = LoginWorker()
        self._login_worker.data_sent.connect(self.login_worker_callback)

        self._pools_worker = PoolsWorker()
        self._pools_worker.data_sent.connect(self.pools_worker_callback)

        self._pool_fetcher_worker = PoolFetcherWorker()
        self._pool_fetcher_worker.data_sent.connect(self.pool_fetcher_worker_callback)

        self._download_results_worker = DownloadResultsWorker()
        self._download_results_worker.data_sent.connect(self.download_results_worker_callback)

        self._google_worker = GoogleWorker()
        self._google_worker.data_sent.connect(self.google_worker_callback)

        self.connections()

    def connections(self):
        self.pushButtonSend.clicked.connect(self.handle_login)
        self.comboBoxSplitfy.activated[str].connect(self.handle_pool_fetcher)
        self.pushButtonDownloadCSV.clicked.connect(self.handle_csv_download)
        self.actionLoginGoogle.triggered.connect(self.handle_google_login)
        self.actionDisconnectGoogle.triggered.connect(self.handle_disconnect_google)
        self.actionDisconnectGoogle.setEnabled(False)

    def login_worker_callback(self, session):
        self.session = session

        if self._pools_worker.isRunning():
            self._pools_worker.stop()
        else:
            self._login_worker.stop()

            self._pools_worker.set_session(self.session)

            self.labelProgressStatus.setText("Cargando botes...")

            self._pools_worker.start()

    def pools_worker_callback(self, pools):
        self._pools_worker.stop()

        self.open_pools = dict(pools)
        self.comboBoxSplitfy.addItems(pools)

        self.labelProgressStatus.setText("Botes cargados")

        self.stop_progress_bar()

    def pool_fetcher_worker_callback(self, pool_info):
        self._pool_fetcher_worker.stop()

        self.labelBoteValue.setText(pool_info["pool_name"])
        self.labelBoteValue.adjustSize()

        self.labelRecaudadoValue.setText(str(pool_info["money_total_amount"]) + '€')
        self.labelPersonasValue.setText(str(pool_info["people_total_amount"]))

        self.labelProgressStatus.setText("Bote cargado")

        self.stop_progress_bar()

    def download_results_worker_callback(self, text):
        self.stop_progress_bar()
        self.labelProgressStatus.setText(text)

    def google_worker_callback(self, google_results):
        self.actionDisconnectGoogle.setEnabled(True)
        self.actionLoginGoogle.setEnabled(False)
        self._google_worker.stop()
        self.stop_progress_bar()

        self.google_files = google_results

        [self.comboBoxGoogle.addItem(file['name']) for file in google_results]

        self.labelProgressStatus.setText("Datos de Google descargados")

    def handle_login(self):
        if self._login_worker.isRunning():
            self._login_worker.stop()
        else:
            self._login_worker.set_username(self.usernameLineEdit.text())
            self._login_worker.set_password(self.passwordLineEdit.text())
            self._login_worker.set_session(self.session)

            self.init_progress_bar()
            self.labelProgressStatus.setText("Conectando...")

            self._login_worker.start()

    def handle_pool_fetcher(self, pool_to_search):
        if self._pool_fetcher_worker.isRunning():
            self._pools_worker.stop()
        else:
            self._pool_fetcher_worker.set_session(self.session)
            self._pool_fetcher_worker.set_open_pools(self.open_pools)
            self._pool_fetcher_worker.set_pool_to_search(pool_to_search)

            self.init_progress_bar()

            self.labelProgressStatus.setText("Cargando bote: {0}".format(pool_to_search))

            self._pool_fetcher_worker.start()

    def handle_csv_download(self):
        if self._download_results_worker.isRunning():
            self._pools_worker.stop()
        else:
            self._download_results_worker.set_session(self.session)

            url = self.open_pools.get(self.comboBoxSplitfy.currentText())
            self._download_results_worker.set_from_url(url)

            file_diag = QFileDialog()

            filename = QFileDialog.getSaveFileName(file_diag, "Guardar archivo", self.comboBoxSplitfy.currentText())

            self._download_results_worker.set_filename(filename[0])

            self.init_progress_bar()
            self.labelProgressStatus.setText("Descargando archivo...")

            self._download_results_worker.start()

    def handle_google_login(self):
        if self._google_worker.isRunning():
            self._google_worker.stop()
        else:
            self.init_progress_bar()
            self.labelProgressStatus.setText("Descargando datos de Google...")

            self._google_worker.start()

    def handle_disconnect_google(self):
        self._google_worker.remove_credentials()

        self.google_files = None
        self.comboBoxGoogle.clear()

        self.actionDisconnectGoogle.setEnabled(False)
        self.actionLoginGoogle.setEnabled(True)

    def init_progress_bar(self):
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)

    def stop_progress_bar(self):
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_process = MainProcess()
    main_process.show()
    sys.exit(app.exec_())
