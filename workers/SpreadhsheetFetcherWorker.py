from PyQt5 import QtCore
from googleapiclient import discovery


class SpreadsheetFetcherWorker(QtCore.QThread):
    message_sent = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(SpreadsheetFetcherWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QtCore.QMutex()

        self.__http_google_credentials = None
        self.__data_to_send = None
        self.__spreadsheet_to_search = ""
        self.__sheets_dict = {}

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False
        service = discovery.build('sheets', 'v4', http=self.__http_google_credentials)

        spreadsheet = self.get_spreadsheet(service)

        for sheet in spreadsheet.get('sheets', []):
            self.__sheets_dict[sheet['properties']['title']] = {"sheetId": sheet['properties']['sheetId']}

        if "Splitfy" in self.__sheets_dict:
            splitfy_sheet_id = self.__sheets_dict.get("Splitfy")['sheetId']

            _BODY_REQUEST = \
                {
                    "requests": [
                        {
                            "deleteSheet": {
                                "sheetId": splitfy_sheet_id
                            }
                        }
                    ]
                }
            service.spreadsheets().batchUpdate(spreadsheetId=self.__spreadsheet_to_search,
                                               body=_BODY_REQUEST).execute()
            self.execute_routine(service)
        else:
            self.execute_routine(service)

    def execute_routine(self, service):
        _BODY_REQUEST = \
            {
                "requests": [
                    {
                        "addSheet":
                            {
                                "properties":
                                    {
                                        "title": "Splitfy"
                                    }
                            }
                    }
                ]
            }

        service.spreadsheets().batchUpdate(spreadsheetId=self.__spreadsheet_to_search,
                                           body=_BODY_REQUEST).execute()

        spreadsheet = self.get_spreadsheet(service)

        for sheet in spreadsheet.get('sheets', []):
            self.__sheets_dict[sheet['properties']['title']] = {"sheetId": sheet['properties']['sheetId']}

        splitfy_sheet_id = self.__sheets_dict.get("Splitfy")['sheetId']

        _BODY_REQUEST = \
            {
                "requests": [
                    {
                        "pasteData": {
                            "delimiter": ",",
                            "data": self.__data_to_send,
                            "coordinate": {
                                "columnIndex": 0,
                                "rowIndex": 0,
                                "sheetId": splitfy_sheet_id
                            }
                        }
                    }
                ]
            }
        service.spreadsheets().batchUpdate(spreadsheetId=self.__spreadsheet_to_search,
                                           body=_BODY_REQUEST).execute()
        self.message_sent.emit("Datos cargados en la hoja")

    def get_spreadsheet(self, service):
        return service.spreadsheets().get(spreadsheetId=self.__spreadsheet_to_search).execute()

    def set_http_google_credentials(self, http_google_credentials):
        self.__http_google_credentials = http_google_credentials

    def set_spreadsheet_to_search(self, spreadsheet_to_search):
        self.__spreadsheet_to_search = spreadsheet_to_search

    def set_data_to_send(self, data_to_send):
        self.__data_to_send = data_to_send
