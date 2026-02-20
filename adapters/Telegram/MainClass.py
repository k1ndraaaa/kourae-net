from adapters.Telegram.Errors import *
import requests


class TelegramNotifier:
    def __init__(self):
        pass
    def send(
        self, 
        message: str
    ):
        try:
            requests.post(
                #cambiar por el servidor de telegram en lan correspondiente
                "http://192.168.1.72:5000/send",
                json={"message": message}
            )
        except Exception as e:
            raise TelegramError(e)