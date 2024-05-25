import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
import os
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time
import websocket  # 使用websocket_client
import cv2
import time


appid = "f3767b32"
api_secret = "NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5"
api_key ="6eff91ce581e5cb276db75ba91552377"
answer = ""
imageunderstanding_url = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"
text = []


def get_image(output_folder='image', filename='img.jpg'):
    """
    从默认摄像头捕获图像并保存到指定文件夹。

    :param output_folder: 图像保存的文件夹名，默认为'image'
    :param filename: 保存的图像文件名，默认为'img.jpg'
    """
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    save_path = os.path.join(output_folder, filename)

    # 初始化视频捕捉，0通常代表默认摄像头
    cap = cv2.VideoCapture(0)

    # 检查是否成功打开摄像头
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return False

    while True:
        # 读取摄像头画面
        ret, frame = cap.read()

        # 显示画面
        cv2.imshow('Camera Preview', frame)

        # 检查是否有按键输入
        key = cv2.waitKey(1) & 0xFF

        # 按's'键保存当前帧并退出循环
        if key == ord('s'):
            # 构造完整保存路径并保存图片
            save_path = os.path.join(output_folder, filename)
            cv2.imwrite(save_path, frame)
            print(f"Frame saved successfully at {save_path}")
            break

    # 释放资源并关闭所有窗口
    cap.release()
    cv2.destroyAllWindows()
    return save_path


class Ws_Param(object):
    # 初始化
    def __init__(self, APPID, APIKey, APISecret, imageunderstanding_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(imageunderstanding_url).netloc
        self.path = urlparse(imageunderstanding_url).path
        self.ImageUnderstanding_url = imageunderstanding_url

    # 生成url
    def create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        # 拼接鉴权参数，生成url
        url = self.ImageUnderstanding_url + '?' + urlencode(v)
        return url


# 收到websocket错误的处理
def on_error(ws, error):
    print("### error:", error)


# 收到websocket关闭的处理
def on_close(ws,one,two):
    print(" ")


# 收到websocket连接建立的处理
def on_open(ws):
    thread.start_new_thread(run, (ws,))


def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, question= ws.question ))
    ws.send(data)


# 收到websocket消息的处理
def on_message(ws, message):
    data = json.loads(message)
    code = data['header']['code']
    if code != 0:
        print(f'请求错误: {code}, {data}')
        ws.close()
    else:
        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]
        print(content,end ="")
        global answer
        answer += content
        if status == 2:
            ws.close()


def gen_params(appid, question):
    """
    通过appid和用户的提问来生成请参数
    """

    data = {
        "header": {
            "app_id": appid
        },
        "parameter": {
            "chat": {
                "domain": "image",
                "temperature": 0.5,
                "top_k": 4,
                "max_tokens": 2028,
                "auditing": "default"
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
}

    return data


def main(appid, api_key, api_secret, imageunderstanding_url,question):

    wsParam = Ws_Param(appid, api_key, api_secret, imageunderstanding_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
    ws.appid = appid
    #ws.imagedata = imagedata
    ws.question = question
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})


def getText(role, content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = content
    text.append(jsoncon)
    return text


def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length


def checklen(text):
    while (getlength(text[1:])> 8000):
        del text[1]
    return text

if __name__ == '__main__':

    def object_recognition():
        global answer
        global text
        img_path = get_image()
        imagedata = open(img_path, 'rb').read()
        text = [{"role": "user", "content": str(base64.b64encode(imagedata), 'utf-8'), "content_type": "image"}]
        ans = []
        while(1):
            Input = input("\n" +"问:")
            question = checklen(getText("user",Input))
            answer = ""
            print("答:",end = "")
            main(appid, api_key, api_secret, imageunderstanding_url, question)
            getText("assistant", answer)
            ans.append(answer)
            print(ans)


    object_recognition()


