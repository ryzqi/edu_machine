import _thread as thread
import os
import random
import string
import time
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse, urlencode
import ssl
from wsgiref.handlers import format_date_time

import websocket
import openpyxl
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from role_play.role import *


def gen_url(appid, secret, chatid):
    url = 'wss://ai-character.xfyun.cn/api/open/interactivews/'
    timestamp = int(time.time() * 1000)
    signature = ApiAuthAlgorithm.get_signature(appid, secret, timestamp)
    url = url + f"{chatid}" + f'?appId={appid}&timestamp={timestamp}&signature={signature}'
    return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws, *args):
    print("### closed ###")


# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, chatid=ws.chatid, pre_chatid=ws.pre_chatid, input=ws.input,agentid=ws.agentid))
    print(data)
    ws.send(data)


# 收到websocket消息的处理
def on_message(ws, message):# message是接收到的消息
    global buffer
    message_dict = json.loads(message)
    code = message_dict['header']['code']
    if code != 0:
        print(f'请求错误: {code}')
        ws.close()
        msg = "请求错误"
        return msg,400
    else:
        status = message_dict['header']['status']
        buffer = buffer + message_dict['payload']['choices']['text'][0]['content']
        # 实现具体对话即可，而具体的实现逻辑无关紧要
        if status == 2:
            print(buffer)  # 在改为api之后，使用return即可
            ws.close()


def gen_params(appid, chatid, pre_chatid, input,agentid):
    if chatid != pre_chatid:
        data = {
            "header": {
                "app_id": appid,
                "uid": "7c0a0c51c34858b4388ea5316db30eee",
                "agent_id": agentid
            },
            "parameter": {
                "chat": {
                    "chat_id": chatid,
                    "pre_chat_id": pre_chatid
                }
            },
            "payload": {
                "message": {
                    "text": [
                        {
                            "role": "user",
                            "content": input
                        }
                    ]
                }
            }
        }
    else:# 这里的agent id就是人格的id
        data = {
            "header": {
                "app_id": appid,
                "uid": "7c0a0c51c34858b4388ea5316db30eee",
                "agent_id": agentid
            },
            "parameter": {
                "chat": {
                    "chat_id": chatid
                }
            },
            "payload": {
                "message": {
                    "text": []
                }
            }
        }
    print(data)
    return data


# clear_cache完成重新对话的部分
def clear_cache(appid, chatid, secret):
    timestamp = int(time.time() * 1000)
    signature = ApiAuthAlgorithm.get_signature(appid, secret, timestamp)
    headers = {
        "appId": appid,
        "timestamp": str(timestamp),
        "signature": signature
    }
    url = 'https://ai-character.xfyun.cn/api/open/interactive/clear-cache' + f'?appId={appid}&chatId={chatid}'
    response = requests.post(url, headers=headers)
    if response.status_code == 200:  # 这里的状态码是看请求是否发送到了
        response_msg = response.json()
        print(response_msg)
        if response_msg.get("code") != 10000:  # 这里状态码返回10000为成功
            raise Exception(f"删除缓存失败，responseMsg = {response_msg}")
    else:
        print(f"Failed to clear cache: {response.status_code}")


def generate_random_string():
    characters = string.ascii_letters + string.digits  # 包含所有字母和数字
    random_string = ''.join(random.choice(characters) for _ in range(12))
    return random_string


'''
# 这里应该在前端实现语音转文字？
# 具体调用逻辑暂不清楚
def main(appid, secret,agentid):
    global buffer
    chatid = generate_random_string()
    pre_chatid = chatid
    buffer = ""
    full_url = gen_url(appid, secret, chatid)  # 生成鉴权之后的url
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(full_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    iinput = ""
    while (iinput != "EXIT!"):
        ws.appid = appid
        ws.chatid = chatid
        ws.pre_chatid = pre_chatid
        ws.input = iinput
        ws.agentid = agentid
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})  # ws建立连接发送消息
        pre_chatid = chatid
        chatid = generate_random_string()
        iinput = input()
    clear_cache(appid, pre_chatid, secret)


if __name__ == "__main__":
    main(appid="7d21d663",
         secret="N2YyMjkxODgzMGYxZjg1YTNlMDAyYjQx",
         agentid = '4b7595a09eb7af93ceba9b2d1d7926ff')
'''