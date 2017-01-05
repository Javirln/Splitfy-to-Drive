import os

import httplib2
from PyQt5 import QtCore
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


class GoogleWorker(QtCore.QThread):
    data_sent = QtCore.pyqtSignal(object)
    http_google_credentials = QtCore.pyqtSignal(object)

    SCOPES = {
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    }
    CLIENT_SECRET_FILE = 'client_secret.json'
    APPLICATION_NAME = 'Splitfy-Desk'

    def __init__(self, parent=None):
        super(GoogleWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self.__local_results = []
        self.__stored_credentials = None
        self.__http_google_credentials = None

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def get_credentials(self):
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'splitfy-desk-credentials.json')

        self.__stored_credentials = Storage(credential_path)
        credentials = self.__stored_credentials.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(os.getcwd() + '/secrets/' + self.CLIENT_SECRET_FILE,
                                                  self.SCOPES,
                                                  redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            flow.user_agent = self.APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, self.__stored_credentials, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, self.__stored_credentials)
            print('Storing credentials to ' + credential_path)
        return credentials

    def run(self):
        self._stopped = False
        self.__local_results = []
        credentials = self.get_credentials()

        self.__http_google_credentials = credentials.authorize(httplib2.Http())
        self.http_google_credentials.emit(self.__http_google_credentials)

        service = discovery.build('drive', 'v3', http=self.__http_google_credentials)

        results = service.files().list(pageSize=1000, fields="nextPageToken, files(id, name, mimeType)").execute()
        items = results.get('files', [])
        if not items:
            print('No files found.')
        else:
            #print('Files:')
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                    #print('{0} ({1}) - {2}'.format(item['name'], item['id'], item['mimeType']))
                    self.__local_results.append({
                        'name': item['name'],
                        'id': item['id'],
                        'mimeType': item['mimeType']
                    })
            self.data_sent.emit(self.__local_results)

    def remove_credentials(self):
        self.__stored_credentials.delete()
