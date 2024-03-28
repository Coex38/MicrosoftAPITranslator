import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QComboBox,
    QVBoxLayout, QWidget, QMessageBox, QTextEdit
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtNetwork import QNetworkConfigurationManager, QNetworkSession
import requests
import urllib
import uuid
from urllib.parse import urlencode


class Worker(QThread):
    result_ready = pyqtSignal(str, str)

    def __init__(self, func, func_name):
        super().__init__()
        self.func = func
        self.func_name = func_name

    def run(self):
        result = self.func()
        self.result_ready.emit(result, self.func_name)


class SignalManager(QObject):
    worker_result = pyqtSignal(str, str)
    no_text_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.no_text_signal.connect(self.show_no_text_warning)

    def show_no_text_warning(self, func_name):
        QMessageBox.warning(None, "No Text Found",
                            f"No text available for {func_name} translation!")


class TranslatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DGN Translator")
        self.setGeometry(100, 100, 400, 250)
        self.network_manager = QNetworkConfigurationManager()
        self.network_session = QNetworkSession(self.network_manager.defaultConfiguration())
        self.network_session.stateChanged.connect(self.check_internet_connection)
        if self.network_session.state() == QNetworkSession.Connected:
            self.setup_ui()
        else:
            self.network_session.open()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.translate_btn = QPushButton("Translate", self)
        self.translate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.translate_btn.clicked.connect(self.start_translation)

        self.func_combobox = QComboBox(self)
        self.func_combobox.addItem("Translate EN Description")
        self.func_combobox.addItem("Translate AR Description")
        self.func_combobox.addItem("Translate RU Description")
        self.func_combobox.addItem("Translate EN Title")
        self.func_combobox.addItem("Translate AR Title")
        self.func_combobox.addItem("Translate RU Title")

        self.result_textbox = QTextEdit(self)
        self.result_textbox.setReadOnly(True)

        layout.addWidget(self.func_combobox)
        layout.addWidget(self.translate_btn)
        layout.addWidget(self.result_textbox)

        central_widget.setLayout(layout)

        self.thread = None
        self.signal_manager = SignalManager()
        self.signal_manager.worker_result.connect(self.update_result_label)

    def check_internet_connection(self, state):
        if state == QNetworkSession.Connected:
            QMessageBox.information(self, "Connection Status", "Internet connection is established.")
        else:
            QMessageBox.critical(self, "Connection Status", "Internet connection is lost.")

    def update_result_label(self, result, func_name):
        result_text = f"{func_name} result: {result}"
        self.result_textbox.append(result_text)

    def start_translation(self):
        selected_func = self.func_combobox.currentIndex()
        if selected_func == 0:
            self.translate(func1, "Translate EN Description")
        elif selected_func == 1:
            self.translate(func2, "Translate AR Description")
        elif selected_func == 2:
            self.translate(func3, "Translate RU Description")
        elif selected_func == 3:
            self.translate(func4, "Translate EN Title")
        elif selected_func == 4:
            self.translate(func5, "Translate AR Title")
        elif selected_func == 5:
            self.translate(func6, "Translate RU Title")

    def translate(self, func, func_name):
        self.thread = Worker(func, func_name)
        self.thread.result_ready.connect(self.signal_manager.worker_result.emit)
        if func() == "":
            self.signal_manager.no_text_signal.emit(func_name)
            return
        self.thread.start()


def func1():
    data = {
        "ServerName": "176.236.176.155",
        "DatabaseName": "V3_TalipsanAS",
        "UserGroupCode": "DGNM",
        "UserName": "M999",
        "Password": "30083009"
    }
    # API anahtarı ve URL ayarlarının belirlenmesi
    key = "49352e49db02427abcdf9860143a628c"
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    location = "westeurope"

    # API için parametrelerin ve başlık bilgilerinin belirlenmesi
    params = {
        'api-version': '3.0',
        'from': 'tr',
        'to': 'en',
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Çevirilecek ürünlerin metinlerinin saklanacağı liste
    body = []

    # Oturum açma isteği
    login_url = "http://176.236.176.155:1260/IntegratorService/Connect?" + urllib.parse.urlencode(data)
    response = requests.post(login_url, headers=headers, json=data)

    # Oturum açma başarılıysa
    if response.status_code == 200:
        session_id = response.json().get("SessionID")
        print("Session ID:", session_id)

        # Çeviri için prosedür bilgisinin hazırlanması
        procedure_info = {
            "ProcName": "Wholesale.dbo.getTranslateProductDescriptions",
            "Parameters": [
                {"Name": "@LangCode", "Value": "EN"}
            ]
        }

        # Çeviri prosedürünün çalıştırılması
        procedure_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
        response = requests.post(procedure_url, params=params, headers=headers, json=procedure_info)

        # Çeviri prosedürü başarılıysa
        if response.status_code == 200:
            translated_products = response.json()

            # Çevrilmiş ürünlerin metinlerinin alınması ve listeye eklenmesi
            for index, product in enumerate(translated_products):
                body.append({'Text': product['HTMLDescription']})

            # Microsoft Translator API'sine çeviri isteği gönderilmesi
            request = requests.post(endpoint + '/translate', params=params, headers=headers, json=body)
            response = request.json()
            print("Translated Products:", translated_products)

            # Her bir çevrilen ürün için
            for t_index, t_product in enumerate(response):
                print("Current T Product:", t_product)
                translated_text = t_product['translations'][0]['text']
                translated_itemcode = translated_products[t_index]["ItemCode"]
                translated_colorcode = translated_products[t_index]["ColorCode"]

                # setProductDescription prosedürü için gerekli parametrelerin hazırlanması
                procedure_final = {
                    "ProcName": "Wholesale.dbo.setProductDescriptions",
                    "Parameters": [
                        {"Name": "@ProductCode", "Value": translated_itemcode},
                        {"Name": "@ColorCode", "Value": translated_colorcode},
                        {"Name": "@LangCode", "Value": "EN"},
                        {"Name": "@Description", "Value": translated_text}
                    ]
                }

                # setProductDescription prosedürünün çağrılması
                procedure_final_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
                response_final = requests.post(procedure_final_url, params=params, headers=headers,
                                               json=procedure_final)
                print("Result:", t_index)
                print(response_final)
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)
    return "Translated Text 1"


def func2():
    data = {
        "ServerName": "176.236.176.155",
        "DatabaseName": "V3_TalipsanAS",
        "UserGroupCode": "DGNM",
        "UserName": "M999",
        "Password": "30083009"
    }

    # API anahtarı ve URL ayarlarının belirlenmesi
    key = "49352e49db02427abcdf9860143a628c"
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    location = "westeurope"

    # API için parametrelerin ve başlık bilgilerinin belirlenmesi
    params = {
        'api-version': '3.0',
        'from': 'tr',
        'to': 'ar',
        'dir': 'rtl'
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Çevirilecek ürünlerin metinlerinin saklanacağı liste
    body = []

    # Oturum açma isteği
    login_url = "http://176.236.176.155:1260/IntegratorService/Connect?" + urllib.parse.urlencode(data)
    response = requests.post(login_url, headers=headers, json=data)

    # Oturum açma başarılıysa
    if response.status_code == 200:
        session_id = response.json().get("SessionID")
        print("Session ID:", session_id)

        # Çeviri için prosedür bilgisinin hazırlanması
        procedure_info = {
            "ProcName": "Wholesale.dbo.getTranslateProductDescriptions",
            "Parameters": [
                {"Name": "@LangCode", "Value": "AR"}
            ]
        }

        # Çeviri prosedürünün çalıştırılması
        procedure_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
        response = requests.post(procedure_url, params=params, headers=headers, json=procedure_info)

        # Çeviri prosedürü başarılıysa
        if response.status_code == 200:
            translated_products = response.json()

            # Çevrilmiş ürünlerin metinlerinin alınması ve listeye eklenmesi
            for index, product in enumerate(translated_products):
                body.append({'Text': product['HTMLDescription']})

            # Microsoft Translator API'sine çeviri isteği gönderilmesi
            request = requests.post(endpoint + '/translate', params=params, headers=headers, json=body)
            response = request.json()
            print("Translated Products:", translated_products)

            # Her bir çevrilen ürün için
            for t_index, t_product in enumerate(response):
                print("Current T Product:", t_product)
                translated_text = t_product['translations'][0]['text']
                translated_itemcode = translated_products[t_index]["ItemCode"]
                translated_colorcode = translated_products[t_index]["ColorCode"]
                print("Translated Text:", translated_text)
                print("Translated Item Code:", translated_itemcode)
                print("Translated Color Code:", translated_colorcode)

                # setProductDescription prosedürü için gerekli parametrelerin hazırlanması
                procedure_final = {
                    "ProcName": "Wholesale.dbo.setProductDescriptions",
                    "Parameters": [
                        {"Name": "@ProductCode", "Value": translated_itemcode},
                        {"Name": "@ColorCode", "Value": translated_colorcode},
                        {"Name": "@LangCode", "Value": "AR"},
                        {"Name": "@Description", "Value": translated_text}
                    ]
                }

                # setProductDescription prosedürünün çağrılması
                procedure_final_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
                response_final = requests.post(procedure_final_url, params=params, headers=headers,
                                               json=procedure_final)
                print("Result:", t_index)
                print(response_final)

        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)
    return "Translated Text 2"


def func3():
    data = {
        "ServerName": "176.236.176.155",
        "DatabaseName": "V3_TalipsanAS",
        "UserGroupCode": "DGNM",
        "UserName": "M999",
        "Password": "30083009"
    }

    # API anahtarı ve URL ayarlarının belirlenmesi
    key = "49352e49db02427abcdf9860143a628c"
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    location = "westeurope"

    # API için parametrelerin ve başlık bilgilerinin belirlenmesi
    params = {
        'api-version': '3.0',
        'from': 'tr',
        'to': 'ru',
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Çevirilecek ürünlerin metinlerinin saklanacağı liste
    body = []

    # Oturum açma isteği
    login_url = "http://176.236.176.155:1260/IntegratorService/Connect?" + urllib.parse.urlencode(data)
    response = requests.post(login_url, headers=headers, json=data)

    # Oturum açma başarılıysa
    if response.status_code == 200:
        session_id = response.json().get("SessionID")
        print("Session ID:", session_id)

        # Çeviri için prosedür bilgisinin hazırlanması
        procedure_info = {
            "ProcName": "Wholesale.dbo.getTranslateProductDescriptions",
            "Parameters": [
                {"Name": "@LangCode", "Value": "RU"}
            ]
        }

        # Çeviri prosedürünün çalıştırılması
        procedure_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
        response = requests.post(procedure_url, params=params, headers=headers, json=procedure_info)

        # Çeviri prosedürü başarılıysa
        if response.status_code == 200:
            translated_products = response.json()

            # Çevrilmiş ürünlerin metinlerinin alınması ve listeye eklenmesi
            for index, product in enumerate(translated_products):
                body.append({'Text': product['HTMLDescription']})

            # Microsoft Translator API'sine çeviri isteği gönderilmesi
            request = requests.post(endpoint + '/translate', params=params, headers=headers, json=body)
            response = request.json()
            print("Translated Products:", translated_products)

            # Her bir çevrilen ürün için
            for t_index, t_product in enumerate(response):
                print("Current T Product:", t_product)
                translated_text = t_product['translations'][0]['text']
                translated_itemcode = translated_products[t_index]["ItemCode"]
                translated_colorcode = translated_products[t_index]["ColorCode"]

                # setProductDescription prosedürü için gerekli parametrelerin hazırlanması
                procedure_final = {
                    "ProcName": "Wholesale.dbo.setProductDescriptions",
                    "Parameters": [
                        {"Name": "@ProductCode", "Value": translated_itemcode},
                        {"Name": "@ColorCode", "Value": translated_colorcode},
                        {"Name": "@LangCode", "Value": "RU"},
                        {"Name": "@Description", "Value": translated_text}
                    ]
                }

                # setProductDescription prosedürünün çağrılması
                procedure_final_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
                response_final = requests.post(procedure_final_url, params=params, headers=headers,
                                               json=procedure_final)
                print("Result:", t_index)
                print(response_final)

        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)
    return "Translated Text 3"


def func4():
    data = {
        "ServerName": "176.236.176.155",
        "DatabaseName": "V3_TalipsanAS",
        "UserGroupCode": "DGNM",
        "UserName": "M999",
        "Password": "30083009"
    }

    # API anahtarı ve URL ayarlarının belirlenmesi
    key = "49352e49db02427abcdf9860143a628c"
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    location = "westeurope"

    # API için parametrelerin ve başlık bilgilerinin belirlenmesi
    params = {
        'api-version': '3.0',
        'from': 'tr',
        'to': 'en'
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Çevirilecek ürünlerin metinlerinin saklanacağı liste
    body = []

    # Oturum açma isteği
    login_url = "http://176.236.176.155:1260/IntegratorService/Connect?" + urllib.parse.urlencode(data)
    response = requests.post(login_url, headers=headers, json=data)

    # Oturum açma başarılıysa
    if response.status_code == 200:
        session_id = response.json().get("SessionID")
        print("Session ID:", session_id)

        # Çeviri için prosedür bilgisinin hazırlanması
        procedure_info = {
            "ProcName": "Wholesale.dbo.getTranslateProducts",
            "Parameters": [
                {"Name": "@LangCode", "Value": "EN"}
            ]
        }

        # Çeviri prosedürünün çalıştırılması
        procedure_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
        response = requests.post(procedure_url, params=params, headers=headers, json=procedure_info)

        # Çeviri prosedürü başarılıysa
        if response.status_code == 200:
            translated_products = response.json()

            # Çevrilmiş ürünlerin metinlerinin alınması ve listeye eklenmesi
            for index, product in enumerate(translated_products):
                body.append({'Text': product['ProductDescription'].replace("DGN ", "")})

            # Microsoft Translator API'sine çeviri isteği gönderilmesi
            request = requests.post(endpoint + '/translate', params=params, headers=headers, json=body)
            response = request.json()
            print(response)
            print("Translated Products:", translated_products)

            # Her bir çevrilen ürün için
            for t_index, t_product in enumerate(response):
                print("Current T Product:", t_product)
                translated_text = t_product['translations'][0]['text']
                translated_itemcode = translated_products[t_index]["ItemCode"]

                # setProductDescription prosedürü için gerekli parametrelerin hazırlanması
                procedure_final = {
                    "ProcName": "Wholesale.dbo.setProductTitle",
                    "Parameters": [
                        {"Name": "@ProductCode", "Value": translated_itemcode},
                        {"Name": "@LangCode", "Value": "EN"},
                        {"Name": "@Title", "Value": translated_text}
                    ]
                }

                # setProductDescription prosedürünün çağrılması
                procedure_final_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
                response_final = requests.post(procedure_final_url, params=params, headers=headers,
                                               json=procedure_final)
                print("Result:", t_index)
                print(response_final)

        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)
    return "Translated Text 4"


def func5():
    data = {
        "ServerName": "176.236.176.155",
        "DatabaseName": "V3_TalipsanAS",
        "UserGroupCode": "DGNM",
        "UserName": "M999",
        "Password": "30083009"
    }

    # API anahtarı ve URL ayarlarının belirlenmesi
    key = "49352e49db02427abcdf9860143a628c"
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    location = "westeurope"

    # API için parametrelerin ve başlık bilgilerinin belirlenmesi
    params = {
        'api-version': '3.0',
        'from': 'tr',
        'to': 'ar',
        'dir': 'rtl'
    }
    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Çevirilecek ürünlerin metinlerinin saklanacağı liste
    body = []

    # Oturum açma isteği
    login_url = "http://176.236.176.155:1260/IntegratorService/Connect?" + urllib.parse.urlencode(data)
    response = requests.post(login_url, headers=headers, json=data)

    # Oturum açma başarılıysa
    if response.status_code == 200:
        session_id = response.json().get("SessionID")
        print("Session ID:", session_id)

        # Çeviri için prosedür bilgisinin hazırlanması
        procedure_info = {
            "ProcName": "Wholesale.dbo.getTranslateProducts",
            "Parameters": [
                {"Name": "@LangCode", "Value": "AR"}
            ]
        }

        # Çeviri prosedürünün çalıştırılması
        procedure_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
        response = requests.post(procedure_url, params=params, headers=headers, json=procedure_info)

        # Çeviri prosedürü başarılıysa
        if response.status_code == 200:
            translated_products = response.json()

            # Çevrilmiş ürünlerin metinlerinin alınması ve listeye eklenmesi
            for index, product in enumerate(translated_products):
                body.append({'Text': product['ProductDescription'].replace("DGN ", "")})

            # Microsoft Translator API'sine çeviri isteği gönderilmesi
            request = requests.post(endpoint + '/translate', params=params, headers=headers, json=body)
            response = request.json()
            print(response)
            print("Translated Products:", translated_products)

            # Her bir çevrilen ürün için
            for t_index, t_product in enumerate(response):
                print("Current T Product:", t_product)
                translated_text = t_product['translations'][0]['text']
                translated_itemcode = translated_products[t_index]["ItemCode"]

                # setProductDescription prosedürü için gerekli parametrelerin hazırlanması
                procedure_final = {
                    "ProcName": "Wholesale.dbo.setProductTitle",
                    "Parameters": [
                        {"Name": "@ProductCode", "Value": translated_itemcode},
                        {"Name": "@LangCode", "Value": "AR"},
                        {"Name": "@Title", "Value": translated_text}
                    ]
                }

                # setProductDescription prosedürünün çağrılması
                procedure_final_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
                response_final = requests.post(procedure_final_url, params=params, headers=headers,
                                               json=procedure_final)
                print("Result:", t_index)
                print(response_final)

        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)
    return "Translated Text 5"


def func6():
    data = {
        "ServerName": "176.236.176.155",
        "DatabaseName": "V3_TalipsanAS",
        "UserGroupCode": "DGNM",
        "UserName": "M999",
        "Password": "30083009"
    }

    # API anahtarı ve URL ayarlarının belirlenmesi
    key = "49352e49db02427abcdf9860143a628c"
    endpoint = "https://api.cognitive.microsofttranslator.com/"
    location = "westeurope"

    # API için parametrelerin ve başlık bilgilerinin belirlenmesi
    params = {
        'api-version': '3.0',
        'from': 'tr',
        'to': 'ru'
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Çevirilecek ürünlerin metinlerinin saklanacağı liste
    body = []

    # Oturum açma isteği
    login_url = "http://176.236.176.155:1260/IntegratorService/Connect?" + urllib.parse.urlencode(data)
    response = requests.post(login_url, headers=headers, json=data)

    # Oturum açma başarılıysa
    if response.status_code == 200:
        session_id = response.json().get("SessionID")
        print("Session ID:", session_id)

        # Çeviri için prosedür bilgisinin hazırlanması
        procedure_info = {
            "ProcName": "Wholesale.dbo.getTranslateProducts",
            "Parameters": [
                {"Name": "@LangCode", "Value": "RU"}
            ]
        }

        # Çeviri prosedürünün çalıştırılması
        procedure_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
        response = requests.post(procedure_url, params=params, headers=headers, json=procedure_info)

        # Çeviri prosedürü başarılıysa
        if response.status_code == 200:
            translated_products = response.json()

            # Çevrilmiş ürünlerin metinlerinin alınması ve listeye eklenmesi
            for index, product in enumerate(translated_products):
                body.append({'Text': product['ProductDescription'].replace("DGN ", "")})

            # Microsoft Translator API'sine çeviri isteği gönderilmesi
            request = requests.post(endpoint + '/translate', params=params, headers=headers, json=body)
            response = request.json()
            print(response)
            print("Translated Products:", translated_products)

            # Her bir çevrilen ürün için
            for t_index, t_product in enumerate(response):
                print("Current T Product:", t_product)
                translated_text = t_product['translations'][0]['text']
                translated_itemcode = translated_products[t_index]["ItemCode"]

                # setProductDescription prosedürü için gerekli parametrelerin hazırlanması
                procedure_final = {
                    "ProcName": "Wholesale.dbo.setProductTitle",
                    "Parameters": [
                        {"Name": "@ProductCode", "Value": translated_itemcode},
                        {"Name": "@LangCode", "Value": "RU"},
                        {"Name": "@Title", "Value": translated_text}
                    ]
                }

                # setProductDescription prosedürünün çağrılması
                procedure_final_url = f"http://176.236.176.155:1260/(S({session_id}))/IntegratorService/RunProc"
                response_final = requests.post(procedure_final_url, params=params, headers=headers,
                                               json=procedure_final)
                print("Result:", t_index)
                print(response_final)

        else:
            print("Error:", response.status_code)
            print("Response:", response.text)

    else:
        print("Error:", response.status_code)
        print("Response:", response.text)
    return "Translated Text 6"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorWindow()
    window.show()
    sys.exit(app.exec_())
