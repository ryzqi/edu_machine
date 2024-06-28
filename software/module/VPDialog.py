import time
import json
import requests
import ssl
import websocket
import _thread as thread
import random
import string
from flask import Flask, request, jsonify
from role_play.player import ApiAuthAlgorithm

# ROLE_TALK

app = Flask(__name__)
# 这里msg为api返回之后的消息
msg = {
            "message": "",
            "chatid": "",  # 下次仅需要传入chatid就能实现对话
        }
appid = "7d21d663"
secret = "N2YyMjkxODgzMGYxZjg1YTNlMDAyYjQx"
buffer = ""  # 将 buffer 变量设置为全局变量

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
    data = json.dumps(gen_params(appid=ws.appid, chatid=ws.chatid, pre_chatid=ws.pre_chatid, input=ws.input, agentid=ws.agentid))
    print(data)
    ws.send(data)

# 收到websocket消息的处理
def on_message(ws, message):
    global buffer  # 使用全局变量 buffer
    message_dict = json.loads(message)
    code = message_dict['header']['code']
    if code != 0:
        print(f'请求错误: {code}')
        ws.close()
        msg = "请求错误"
        return msg, 400
    else:
        status = message_dict['header']['status']
        buffer += message_dict['payload']['choices']['text'][0]['content']
        # 实现具体对话即可，而具体的实现逻辑无关紧要
        if status == 2:
            print(buffer)  # 在改为api之后，使用return即可
            ws.close()

def gen_params(appid, chatid, pre_chatid, input, agentid):
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
    else:
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
    if response.status_code == 200:
        response_msg = response.json()
        print(response_msg)
        if response_msg.get("code") != 10000:
            raise Exception(f"删除缓存失败，responseMsg = {response_msg}")
    else:
        print(f"Failed to clear cache: {response.status_code}")

def generate_random_string():
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(12))
    return random_string

@app.route("/talk", methods=['POST'])
def talk_moli():
    global buffer  # 使用全局变量 buffer

    data = request.get_json()
    msg = data['msg']
    chatid = data['chatid']
    pre_chatid = data['prechatid']
    agentid = data['agentid']
    buffer = ""
    full_url = gen_url(appid, secret, chatid)
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(full_url, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.appid = appid
    ws.chatid = chatid
    ws.pre_chatid = pre_chatid
    ws.input = msg
    ws.agentid = agentid
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    #print("hello")
    #print(buffer)
    #clear_cache(appid, chatid, secret)
    msg = {
        "message": buffer,
        "chatid": chatid,  # 下次仅需要传入chatid就能实现对话
    }
    return msg,200

@app.route('/end',methods=['post'])
def end():
    data = request.get_json()
    agentid = data['agentid']
    chatid = data['chatid']
    clear_cache(appid,chatid,secret)
    return 'Success',200


if __name__ == "__main__":
    app.run(debug=True)
