
import xml.etree.ElementTree as ET
from builtins import Exception, str, bytes
import websocket
import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
import _thread as thread
import queue

STATUS_FIRST_FRAME = 0  # 第一帧的标识
STATUS_CONTINUE_FRAME = 1  # 中间帧标识
STATUS_LAST_FRAME = 2  # 最后一帧的标识

#  BusinessArgs参数常量
SUB = "ise"

result_queue = queue.Queue()


class Ws_Param:
    def __init__(self, APPID, APIKey, APISecret, AudioFile, Text, CATEGORY, ENT):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.AudioFile = AudioFile
        self.Text = Text

        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {
            "category": CATEGORY,
            "sub": SUB,
            "ent": ENT,
            "cmd": "ssb",
            "auf": "audio/L16;rate=16000",
            "aue": "raw",
            "text": self.Text,
            "ttp_skip": True,
            "aus": 1
        }

    def create_url(self):
        url = 'ws://ise-api.xfyun.cn/v2/open-ise'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: ise-api.xfyun.cn\n"
        signature_origin += f"date: {date}\nGET /v2/open-ise HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')

        authorization_origin = f"api_key=\"{self.APIKey}\", algorithm=\"hmac-sha256\", headers=\"host date request-line\", signature=\"{signature_sha}\""
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": "ise-api.xfyun.cn"
        }
        url += '?' + urlencode(v)
        return url


def on_message(ws, message):
    try:
        code = json.loads(message)["code"]
        sid = json.loads(message)["sid"]
        if code != 0:
            errMsg = json.loads(message)["message"]
            print(f"sid:{sid} call error:{errMsg} code is:{code}")
        else:
            data = json.loads(message)["data"]
            status = data["status"]
            result = data["data"]
            if status == 2:
                xml = base64.b64decode(result)
                decoded_xml = xml.decode("gbk")
                result_queue.put(decoded_xml)
    except Exception as e:
        print("receive msg,but parse exception:", e)


def on_error(ws, error):
    print(f"### error:{error}")


def on_close(ws, *args):
    print("### closed ###")


def on_open(ws, wsParam):
    def run():
        frameSize = 1280
        intervel = 0.04
        status = STATUS_FIRST_FRAME

        with open(wsParam.AudioFile, "rb") as fp:
            while True:
                buf = fp.read(frameSize)
                if not buf:
                    status = STATUS_LAST_FRAME
                if status == STATUS_FIRST_FRAME:
                    d = {"common": wsParam.CommonArgs, "business": wsParam.BusinessArgs, "data": {"status": 0}}
                    ws.send(json.dumps(d))
                    status = STATUS_CONTINUE_FRAME
                elif status == STATUS_CONTINUE_FRAME:
                    d = {"business": {"cmd": "auw", "aus": 2, "aue": "raw"},
                         "data": {"status": 1, "data": str(base64.b64encode(buf).decode())}}
                    ws.send(json.dumps(d))
                elif status == STATUS_LAST_FRAME:
                    d = {"business": {"cmd": "auw", "aus": 4, "aue": "raw"},
                         "data": {"status": 2, "data": str(base64.b64encode(buf).decode())}}
                    ws.send(json.dumps(d))
                    time.sleep(1)
                    break
                time.sleep(intervel)
        ws.close()

    thread.start_new_thread(run, ())


def parse_xml(xml_data):
    # 解析XML数据
    root = ET.fromstring(xml_data)

    # 查找sentence元素
    sentence_element = root.find('.//sentence')

    # 提取所需信息
    sentence_info = {
        '准确度分': sentence_element.get('accuracy_score'),
        '标准度分': sentence_element.get('standard_score'),
        '流畅度分': sentence_element.get('fluency_score'),
        '总分': sentence_element.get('total_score')
    }
    return sentence_info


def voice_review(ENT, CATEGORY, TEXT, AudioFile):
    #  英文：en_vip

    # 英文题型：read_sentence（句子朗读）

    # 待评测文本 utf8 编码，需要加utf8bom 头
    TEXT = '\uFEFF' + TEXT

    wsParam = Ws_Param(APPID='f3767b32', APISecret='NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5',
                       APIKey='6eff91ce581e5cb276db75ba91552377',
                       AudioFile=AudioFile, Text=TEXT, CATEGORY=CATEGORY, ENT=ENT)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, on_message=on_message, on_error=on_error, on_close=on_close,
                                on_open=lambda ws: on_open(ws, wsParam))
    websocket.enableTrace(False)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    # 等待直到队列中有至少一个元素
    while result_queue.empty():
        time.sleep(0.1)  # 可选：小延迟避免过度占用CPU

    # 获取并返回第一个结果
    decoded_xml = result_queue.get()
    decoded_xml = parse_xml(decoded_xml)
    return decoded_xml


# xml = voice_review("en_vip", "read_sentence", 'How are you?', "audio/audio.pcm")
# print(xml)
# {'准确度分': '3.552058', '标准度分': '3.330751', '流畅度分': '3.711770', '总分': '3.577841'}
