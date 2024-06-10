# -*- encoding:utf-8 -*-
import hashlib
import hmac
import base64
from socket import *
import json, time, threading
from websocket import create_connection
import websocket
from urllib.parse import quote
import logging


class Client():
    def __init__(self):
        base_url = "ws://rtasr.xfyun.cn/v1/ws"
        ts = str(int(time.time()))
        tt = (app_id + ts).encode('utf-8')
        md5 = hashlib.md5()
        md5.update(tt)
        baseString = md5.hexdigest()
        baseString = bytes(baseString, encoding='utf-8')

        apiKey = api_key.encode('utf-8')
        signa = hmac.new(apiKey, baseString, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        self.end_tag = "{\"end\": true}"

        self.ws = create_connection(base_url + "?appid=" + app_id + "&ts=" + ts + "&signa=" + quote(signa))
        self.trecv = threading.Thread(target=self.recv)
        self.trecv.start()
        self.collected_results = []  # 初始化一个列表来存储所有结果

    def send(self, file_path):
        file_object = open(file_path, 'rb')
        try:
            index = 1
            while True:
                chunk = file_object.read(1280)
                if not chunk:
                    break
                self.ws.send(chunk)

                index += 1
                time.sleep(0.04)
        finally:
            file_object.close()

        self.ws.send(bytes(self.end_tag.encode('utf-8')))


    def recv(self):
        try:
            while self.ws.connected:
                result = str(self.ws.recv())
                if len(result) == 0:
                    break
                result_dict = json.loads(result)
                # 解析结果

                if result_dict["action"] == "result":
                    result_1 = result_dict
                    self.collected_results.append(result_1["data"])      # 收集结果

                if result_dict["action"] == "error":

                    self.ws.close()
                    return
        except websocket.WebSocketConnectionClosedException:
            ...

    def close(self):
        self.ws.close()



if __name__ == '__main__':
    logging.basicConfig()

    app_id = "f3767b32"
    api_key = "ac35bc0461b933c2e81d28ca08d3cb20"
    file_path = 'soundfile/output.pcm'

    client = Client()
    client.send(file_path)
    result = client.collected_results



