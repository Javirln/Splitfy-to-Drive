#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from workers.SpreadhsheetFetcherWorker import SpreadsheetFetcherWorker


class MainProcess(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        uic.loadUi("splitfy-core.ui", self)

        # Class variables
        self.open_pools = {}
        self.google_files = None
        self.session = requests.session()
        self.http_google_credentials = None
        self.google_combo_value = None
        self.splitfy_combo_value = ""
        self.data_to_send = ""

        # Workers
        self.__login_worker = LoginWorker()
        self.__login_worker.data_sent.connect(self.login_worker_callback)

        self.__pools_worker = PoolsWorker()
        self.__pools_worker.data_sent.connect(self.pools_worker_callback)

        self.__pool_fetcher_worker = PoolFetcherWorker()
        self.__pool_fetcher_worker.data_sent.connect(self.pool_fetcher_worker_callback)

        self.__download_results_worker = DownloadResultsWorker()
        self.__download_results_worker.send_message.connect(self.download_results_worker_message_callback)
        self.__download_results_worker.data_send.connect(self.download_results_worker_callback)

        self.__google_worker = GoogleWorker()
        self.__google_worker.data_sent.connect(self.google_worker_callback)
        self.__google_worker.http_google_credentials.connect(self.http_google_credentials_callback)

        self.__google_spreadsheet_worker = SpreadsheetFetcherWorker()
        self.__google_spreadsheet_worker.message_sent.connect(self.google_spreadsheet_worker_callback)

        self.connections()

    def connections(self):
        # Buttons
        self.pushButtonSend.clicked.connect(self.handle_login)
        self.pushButtonDownloadCSV.clicked.connect(self.handle_csv_download)
        self.pushButtonSendToGoogle.clicked.connect(self.handle_google_fetcher)

        # Combobox
        self.comboBoxSplitfy.currentIndexChanged[str].connect(self.set_splitfy_combo_value)
        self.comboBoxGoogle.currentIndexChanged[str].connect(self.set_google_combo_value)

        # Menu buttons
        self.actionLoginGoogle.triggered.connect(self.handle_google_login)
        self.actionDisconnectGoogle.triggered.connect(self.handle_disconnect_google)
        self.actionDisconnectGoogle.setEnabled(False)

    def login_worker_callback(self, session):
        self.session = session

        if self.__pools_worker.isRunning():
            self.__pools_worker.stop()
        else:
            self.__login_worker.stop()

            self.__pools_worker.set_session(self.session)

            self.labelProgressStatus.setText("Cargando botes...")

            self.__pools_worker.start()

    def pools_worker_callback(self, pools):
        self.__pools_worker.stop()

        self.open_pools = dict(pools)
        self.comboBoxSplitfy.addItems(pools)

        self.labelProgressStatus.setText("Botes cargados")

        self.stop_progress_bar()

    def pool_fetcher_worker_callback(self, pool_info):
        self.__pool_fetcher_worker.stop()

        self.labelBoteValue.setText(pool_info["pool_name"])
        self.labelBoteValue.adjustSize()

        self.labelRecaudadoValue.setText(str(pool_info["money_total_amount"]) + '€')
        self.labelPersonasValue.setText(str(pool_info["people_total_amount"]))

        self.labelProgressStatus.setText("Bote cargado")
        self.stop_progress_bar()

    def download_results_worker_message_callback(self, text):
        self.__download_results_worker.stop()
        self.stop_progress_bar()
        self.labelProgressStatus.setText(text)

    def download_results_worker_callback(self, data):
        self.__download_results_worker.stop()
        self.data_to_send = data

        self.handle_google_fetcher()

    def google_worker_callback(self, google_results):
        self.actionDisconnectGoogle.setEnabled(True)
        self.actionLoginGoogle.setEnabled(False)
        self.__google_worker.stop()
        self.stop_progress_bar()

        self.google_files = google_results

        [self.comboBoxGoogle.addItem(file['name']) for file in self.google_files]

        self.labelProgressStatus.setText("Datos de Google descargados")

    def http_google_credentials_callback(self, credentials):
        self.http_google_credentials = credentials

    def google_spreadsheet_worker_callback(self, message):
        self.__google_spreadsheet_worker.stop()
        self.data_to_send = ""
        self.stop_progress_bar()
        self.labelProgressStatus.setText(message)

    def handle_login(self):
        if self.__login_worker.isRunning():
            self.__login_worker.stop()
        else:
            if self.handle_blank_none(self.usernameLineEdit.text()) and self.handle_blank_none(
                    self.passwordLineEdit.text()):
                self.__login_worker.set_username(self.usernameLineEdit.text())
                self.__login_worker.set_password(self.passwordLineEdit.text())
                self.__login_worker.set_session(self.session)

                self.init_progress_bar()
                self.labelProgressStatus.setText("Conectando...")

                self.__login_worker.start()
            else:
                self.labelProgressStatus.setText("El usuario y contraseña no pueden estar en blanco")

    def handle_pool_fetcher(self, pool_to_search):
        if self.__pool_fetcher_worker.isRunning():
            self.__pools_worker.stop()
        else:
            self.__pool_fetcher_worker.set_session(self.session)
            self.__pool_fetcher_worker.set_open_pools(self.open_pools)
            self.__pool_fetcher_worker.set_pool_to_search(pool_to_search)

            self.init_progress_bar()

            self.labelProgressStatus.setText("Cargando bote: {0}".format(pool_to_search))

            self.__pool_fetcher_worker.start()

    def handle_csv_download(self):
        if self.__download_results_worker.isRunning():
            self.__pools_worker.stop()
        else:
            if self.handle_blank_none(self.splitfy_combo_value):
                self.__download_results_worker.set_session(self.session)

                url = self.splitfy_pool_url()
                self.__download_results_worker.set_from_url(url)

                file_diag = QFileDialog()

                filename = QFileDialog.getSaveFileName(file_diag, "Guardar archivo", self.comboBoxSplitfy.currentText())

                self.__download_results_worker.set_filename(filename[0])

                self.init_progress_bar()
                self.labelProgressStatus.setText("Descargando archivo...")

                self.__download_results_worker.set_is_to_googe(False)

                self.__download_results_worker.start()
            else:
                self.labelProgressStatus.setText("Tienes que hacer login en Splitfy antes de continuar")

    def handle_google_login(self):
        if self.__google_worker.isRunning():
            self.__google_worker.stop()
        else:
            self.init_progress_bar()
            self.labelProgressStatus.setText("Descargando datos de Google...")

            self.__google_worker.start()

    def handle_disconnect_google(self):
        self.__google_worker.remove_credentials()

        self.google_files = None
        self.comboBoxGoogle.clear()

        self.actionDisconnectGoogle.setEnabled(False)
        self.actionLoginGoogle.setEnabled(True)

    def handle_google_fetcher(self):
        if self.__google_spreadsheet_worker.isRunning():
            self.__google_spreadsheet_worker.stop()
        else:
            if self.handle_blank_none(self.google_combo_value):
                self.__google_spreadsheet_worker.set_http_google_credentials(self.http_google_credentials)
                spreadsheet_name = self.google_combo_value

                if self.data_to_send == "":
                    self.__download_results_worker.set_is_to_googe(True)
                    url = self.splitfy_pool_url()
                    self.__download_results_worker.set_from_url(url)
                    self.__download_results_worker.set_session(self.session)

                    self.__download_results_worker.start()

                else:
                    for spreadsheet in self.google_files:
                        if spreadsheet['name'] == spreadsheet_name:
                            self.__google_spreadsheet_worker.set_spreadsheet_to_search(spreadsheet['id'])

                            self.labelProgressStatus.setText("Enviando datos al archivo: {0}".format(spreadsheet_name))
                            self.init_progress_bar()

                            self.__google_spreadsheet_worker.set_data_to_send(self.data_to_send)

                            # The payload must be cleared since in future call might produce errors
                            self.data_to_send = ""

                            self.__google_spreadsheet_worker.start()
                            break
                        else:
                            self.labelProgressStatus.setText("Error interno")
            else:
                self.labelProgressStatus.setText("Tienes que hacer login en Google antes de continuar")

    def init_progress_bar(self):
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)

    def stop_progress_bar(self):
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1)

    def set_google_combo_value(self, spreadsheet_to_search):
        self.google_combo_value = spreadsheet_to_search

    def set_splitfy_combo_value(self, pool_to_search):
        self.splitfy_combo_value = pool_to_search

        # Call the worker to initialize the thread
        self.handle_pool_fetcher(self.splitfy_combo_value)

    def splitfy_pool_url(self):
        return self.open_pools.get(self.comboBoxSplitfy.currentText())

    def handle_blank_none(self, object):
        return not object == "" and object is not None


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_process = MainProcess()
    main_process.show()
    sys.exit(app.exec_())
