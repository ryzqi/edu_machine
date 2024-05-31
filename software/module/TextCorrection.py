# -*- coding:utf-8 -*-
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import requests


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(this, host, path, schema):
        this.host = host
        this.path = path
        this.schema = schema
        pass


class WebsocketDemo:
    def __init__(self, APPId, APISecret, APIKey, Text):
        self.appid = APPId
        self.apisecret = APISecret
        self.apikey = APIKey
        self.text = Text
        self.url = 'https://api.xf-yun.com/v1/private/s9a87e3ec'

    # calculate sha256 and encode to base64
    def sha256base64(self, data):
        sha256 = hashlib.sha256()
        sha256.update(data)
        digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
        return digest

    def parse_url(self, requset_url):
        stidx = requset_url.index("://")
        host = requset_url[stidx + 3:]
        schema = requset_url[:stidx + 3]
        edidx = host.index("/")
        if edidx <= 0:
            raise AssembleHeaderException("invalid request url:" + requset_url)
        path = host[edidx:]
        host = host[:edidx]
        u = Url(host, path, schema)
        return u

    # build websocket auth request url
    def assemble_ws_auth_url(self, requset_url, method="POST", api_key="", api_secret=""):
        u = self.parse_url(requset_url)
        host = u.host
        path = u.path
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)

        signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            api_key, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # print(authorization_origin)
        values = {
            "host": host,
            "date": date,
            "authorization": authorization
        }

        return requset_url + "?" + urlencode(values)

    def get_body(self):
        body = {
            "header": {
                "app_id": self.appid,
                "status": 3,
                # "uid":"your_uid"
            },
            "parameter": {
                "s9a87e3ec": {
                    # "res_id":"your_res_id",
                    "result": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "json"
                    }
                }
            },
            "payload": {
                "input": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "status": 3,
                    "text": base64.b64encode(self.text.encode("utf-8")).decode('utf-8')
                }
            }
        }
        return body

    def get_result(self):
        request_url = self.assemble_ws_auth_url(self.url, "POST", self.apikey, self.apisecret)
        headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'app_id': self.appid}
        body = self.get_body()
        response = requests.post(request_url, data=json.dumps(body), headers=headers)
        # print('onMessage：\n' + response.content.decode())
        tempResult = json.loads(response.content.decode())
        return base64.b64decode(tempResult['payload']['result']['text']).decode()


def format_error_report(error_details):
    formatted_report = ""

    # 定义错误类型的中文翻译映射
    error_types = {
        "black_list": "黑名单词汇",
        "pol": "政治术语",
        "char": "别字",
        "word": "别词",
        "redund": "冗余",
        "miss": "缺失",
        "order": "乱序",
        "dapei": "搭配",
        "punc": "标点",
        "idm": "成语",
        "org": "机构名",
        "leader": "领导人职称",
        "number": "数字",
        "addr": "地名",
        "name": "人名",
        "grammar_pc": "句式杂糅/语义重复"
    }

    for error_type, errors in error_details.items():
        # 添加条件判断来忽略“标点错误”
        if error_type != "punc" and errors:
            formatted_report += f"\n--- {error_types.get(error_type, '未知错误类型')} ---\n"
            for error in errors:
                position, original, corrected, desc = error
                formatted_report += f"位置：{position}，原文：'{original}'，更正为：'{corrected}'\n"

    return formatted_report.strip()


# 控制台获取
APPId = "f3767b32"
APISecret = "NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5"
APIKey = "6eff91ce581e5cb276db75ba91552377"


def text_correction(text):
    # 需纠错文本
    Text = text
    demo = WebsocketDemo(APPId, APISecret, APIKey, Text)
    result = json.loads(demo.get_result())

    return format_error_report(result)

