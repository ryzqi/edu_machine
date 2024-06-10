#   gevent==1.4.0
#   greenlet==0.4.15
#   pycparser==2.19
#   six==1.12.0
#   websocket==0.2.1
#   websocket-client==0.56.0
#

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


def voice_review(ENT, CATEGORY, TEXT, AudioFile):
    # 中文：cn_vip， 英文：en_vip

    # 中文题型：read_syllable（单字朗读，汉语专有）read_word（词语朗读）
    # read_sentence（句子朗读）read_chapter(篇章朗读)
    # 英文题型：read_word（词语朗读）read_sentence（句子朗读）read_chapter(篇章朗读)
    # simple_expression（英文情景反应）

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
    return decoded_xml


# xml = voice_review("cn_vip", "read_sentence", '今天天气怎么样？', "read_sentence_cn.pcm")


# <?xml version="1.0" encoding="UTF-8"?>
#   <xml_result>
#       <read_sentence lan="cn" type="study" version="7,0,0,1024">
#           <rec_paper>
#               <read_sentence accuracy_score="0.000000" beg_pos="0" content="今天天气怎么样。" emotion_score="0.000000" end_pos="146" except_info="0" fluency_score="81.685753" integrity_score="100.000000" is_rejected="false" phone_score="78.571426" time_len="146" tone_score="100.000000" total_score="81.539688">
#                   <sentence beg_pos="0" content="今天天气怎么样" end_pos="146" fluency_score="0.000000" phone_score="78.571426" time_len="146" tone_score="100.000000" total_score="58.599205">
#                       <word beg_pos="0" content="今" end_pos="9" symbol="jin1" time_len="9">
#                           <syll beg_pos="0" content="fil" dp_message="32" end_pos="1" rec_node_type="fil" time_len="1">
#                               <phone beg_pos="0" content="fil" dp_message="32" end_pos="1" rec_node_type="fil" time_len="1"></phone>
#                           </syll>
#                           <syll beg_pos="1" content="今" dp_message="0" end_pos="9" rec_node_type="paper" symbol="jin1" time_len="8">
#                               <phone beg_pos="1" content="j" dp_message="0" end_pos="4" is_yun="0" perr_level_msg="3" perr_msg="1" rec_node_type="paper" time_len="3"></phone>
#                               <phone beg_pos="4" content="in" dp_message="0" end_pos="9" is_yun="1" mono_tone="TONE1" perr_level_msg="3" perr_msg="1" rec_node_type="paper" time_len="5"></phone>
#                           </syll>
#                       </word>
#                       <word beg_pos="9" content="天" end_pos="36" symbol="tian1" time_len="27">
#                           <syll beg_pos="9" content="天" dp_message="0" end_pos="36" rec_node_type="paper" symbol="tian1" time_len="27">
#                               <phone beg_pos="9" content="t" dp_message="0" end_pos="25" is_yun="0" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="16"></phone>
#                               <phone beg_pos="25" content="ian" dp_message="0" end_pos="36" is_yun="1" mono_tone="TONE1" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="11"></phone>
#                           </syll>
#                       </word>
#                       <word beg_pos="36" content="天" end_pos="54" symbol="tian1" time_len="18">
#                           <syll beg_pos="36" content="天" dp_message="0" end_pos="54" rec_node_type="paper" symbol="tian1" time_len="18">
#                               <phone beg_pos="36" content="t" dp_message="0" end_pos="42" is_yun="0" perr_level_msg="2" perr_msg="0" rec_node_type="paper" time_len="6"></phone>
#                               <phone beg_pos="42" content="ian" dp_message="0" end_pos="54" is_yun="1" mono_tone="TONE1" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="12"></phone>
#                           </syll>
#                       </word>
#                       <word beg_pos="54" content="气" end_pos="70" symbol="qi9" time_len="16">
#                           <syll beg_pos="54" content="气" dp_message="0" end_pos="70" rec_node_type="paper" symbol="qi0" time_len="16">
#                               <phone beg_pos="54" content="q" dp_message="0" end_pos="62" is_yun="0" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="8"></phone>
#                               <phone beg_pos="62" content="i" dp_message="0" end_pos="70" is_yun="1" mono_tone="TONE0" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="8"></phone>
#                           </syll>
#                       </word>
#                       <word beg_pos="70" content="怎" end_pos="80" symbol="zen3" time_len="10">
#                           <syll beg_pos="70" content="怎" dp_message="0" end_pos="80" rec_node_type="paper" symbol="zen3" time_len="10">
#                               <phone beg_pos="70" content="z" dp_message="0" end_pos="75" is_yun="0" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="5"></phone>
#                               <phone beg_pos="75" content="en" dp_message="0" end_pos="80" is_yun="1" mono_tone="TONE3" perr_level_msg="3" perr_msg="1" rec_node_type="paper" time_len="5"></phone>
#                           </syll>
#                       </word>
#                       <word beg_pos="80" content="么" end_pos="89" symbol="me5" time_len="9">
#                           <syll beg_pos="80" content="么" dp_message="0" end_pos="89" rec_node_type="paper" symbol="me0" time_len="9">
#                               <phone beg_pos="80" content="m" dp_message="0" end_pos="84" is_yun="0" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="4"></phone>
#                               <phone beg_pos="84" content="e" dp_message="0" end_pos="89" is_yun="1" mono_tone="TONE0" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="5"></phone>
#                           </syll>
#                       </word>
#                       <word beg_pos="89" content="样" end_pos="146" symbol="yang4" time_len="57">
#                           <syll beg_pos="89" content="样" dp_message="0" end_pos="108" rec_node_type="paper" symbol="yang4" time_len="19">
#                               <phone beg_pos="89" content="_i" dp_message="0" end_pos="92" is_yun="0" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="3"></phone>
#                               <phone beg_pos="92" content="iang" dp_message="0" end_pos="108" is_yun="1" mono_tone="TONE4" perr_level_msg="1" perr_msg="0" rec_node_type="paper" time_len="16"></phone>
#                           </syll>
#                           <syll beg_pos="108" content="sil" dp_message="0" end_pos="146" rec_node_type="sil" time_len="38">
#                               <phone beg_pos="108" content="sil" end_pos="146" time_len="38"></phone>
#                           </syll>
#                       </word>
#                   </sentence>
#               </read_sentence>
#           </rec_paper>
#       </read_sentence>
#   </xml_result>