import sys
import hashlib
from hashlib import sha1
import hmac
import base64
from socket import *
import json, time, threading
from websocket import create_connection
import websocket
from urllib.parse import quote
import logging
import unicodedata

logging.basicConfig()

base_url = "ws://rtasr.xfyun.cn/v1/ws"
app_id = "5f261727"
api_key = "b697bdd16dfa78d703cc70a871f3656e"

end_tag = "{\"end\": true}"


class Client():
    def __init__(self):
        # 生成鉴权参数
        ts = str(int(time.time()))
        tmp = app_id + ts
        hl = hashlib.md5()
        hl.update(tmp.encode(encoding='utf-8'))
        my_sign = hmac.new(api_key.encode(), hl.hexdigest().encode(), sha1).digest()
        signa = base64.b64encode(my_sign)

        # Create WebSocket connection
        self.ws = create_connection(
            base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa.decode('utf-8')))
        self.trecv = threading.Thread(target=self.recv)
        self.trecv.start()
        self.data = []

    def send(self, file_path):
        with open(file_path, 'rb') as file_object:
            index = 1
            while True:
                chunk = file_object.read(1280)
                if not chunk:
                    break
                self.ws.send(chunk)
                index += 1
                time.sleep(0.04)

        self.ws.send(bytes(end_tag, encoding='utf-8'))
        print("send end tag success")

    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    print("receive result end")
                    # print(data)
                    break
                result_dict = json.loads(result)

                # Print different messages based on action type
                if result_dict["action"] == "started":
                    ...
                    # print("handshake success, result: " + result)

                if result_dict["action"] == "result":
                    # print("rtasr result: " + result)
                    self.data = result_dict['data']

                if result_dict["action"] == "error":
                    print("rtasr error: " + result)
                    self.ws.close()
                    return
        except websocket.WebSocketConnectionClosedException:
            print("receive result end")  # 返回多个是因为使用的是websocket通信框架

    def close(self):
        self.ws.close()
        self.data = []
        print("connection closed")


# file_path = "audio/audio.pcm"


def audio_to_text(file_path):
    client = Client()
    client.send(file_path)
    text = gettext(client.data)
    return text


def gettext(data_dict):
    data_dict = json.loads(data_dict)
    words = [char_word['w'] for item in data_dict['cn']['st']['rt'][0]['ws'] for char_word in item['cw']]
    text = ''.join(words)
    return text


# audio_to_text(file_path)
