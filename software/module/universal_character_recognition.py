from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import hashlib
import base64
import hmac
from urllib.parse import urlencode
import json
import requests
from PIL import Image, ImageDraw

'''
1、通用文字识别,图像数据base64编码后大小不得超过10M
3、支持中英文,支持手写和印刷文字。
4、在倾斜文字上效果有提升，同时支持部分生僻字的识别
'''

APPId = "f3767b32"  # 控制台获取
APISecret = "NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5"  # 控制台获取
APIKey = "6eff91ce581e5cb276db75ba91552377"  # 控制台获取


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema
        pass


# calculate sha256 and encode to base64
def sha256base64(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(requset_url):
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
def assemble_ws_auth_url(requset_url, method="POST", api_key="", api_secret=""):
    u = parse_url(requset_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    # print(date)

    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    # print(signature_origin)
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


url = 'https://api.xf-yun.com/v1/private/sf8e6aca1'


# 传入图片保存在ocr文件夹下
def ocr(image_path):
    with open(image_path, "rb") as f:
        imageBytes = f.read()

    body = {
        "header": {
            "app_id": APPId,
            "status": 3
        },
        "parameter": {
            "sf8e6aca1": {
                "category": "ch_en_public_cloud",
                "result": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "sf8e6aca1_data_1": {
                "encoding": "jpg",
                "image": str(base64.b64encode(imageBytes), 'UTF-8'),
                "status": 3
            }
        }
    }

    request_url = assemble_ws_auth_url(url, "POST", APIKey, APISecret)

    headers = {'content-type': "application/json", 'host': 'api.xf-yun.com', 'app_id': APPId}

    response = requests.post(request_url, data=json.dumps(body), headers=headers)

    tempResult = json.loads(response.content.decode())

    finalResult = base64.b64decode(tempResult['payload']['result']['text']).decode()
    finalResult = finalResult.replace(" ", "").replace("\n", "").replace("\t", "").strip()

    tempResult = json.loads(finalResult)
    # 打开图片
    image_path = image_path
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    result = []
    # 遍历识别结果中的每一页和每行文字
    for page in tempResult['pages']:
        for line in page['lines']:
            # 提取文字内容和坐标
            words = line.get('words', '无文字内容')  # 如果'words'不存在，则默认显示'无文字内容'
            result.append(words[0]['content'])
            coord = line['coord']

            # 计算文字框的左上角和右下角坐标
            x1, y1 = coord[0]['x'], coord[0]['y']
            x2, y2 = coord[2]['x'], coord[2]['y']

            # 在图片上画出矩形框
            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)  # 红色边框，宽度为3

    # 保存处理后的图片
    image.save('ocr/result.jpg')

    return result
    # ['夜景', '拍照', '人像']


# ocr('ocr/1.jpg')