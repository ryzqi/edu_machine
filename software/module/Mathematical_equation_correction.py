import os

import cv2
import requests
import datetime
import hashlib
import base64
import hmac
import json
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def get_image(output_folder='itr', filename='itr.jpg'):
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


class get_result(object):
    def __init__(self, host):
        # 应用ID（到控制台获取）
        self.APPID = "f3767b32"  # 请替换为你的APPID
        # 接口APISercet（到控制台拍照速算服务页面获取）
        self.Secret = "NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5"  # 请替换为你的Secret
        # 接口APIKey（到控制台拍照速算服务页面获取）
        self.APIKey = "6eff91ce581e5cb276db75ba91552377"  # 请替换为你的APIKey
        # 以下为POST请求
        self.Host = host
        self.RequestUri = "/v2/itr"
        self.url = "https://" + host + self.RequestUri
        self.HttpMethod = "POST"
        self.Algorithm = "hmac-sha256"
        self.HttpProto = "HTTP/1.1"

        # 设置当前时间
        curTime_utc = datetime.datetime.utcnow()
        self.Date = self.httpdate(curTime_utc)
        # 设置测试图片文件
        self.AudioPath = "itr/itr.jpg"  # 请替换为你的图片路径
        self.BusinessArgs = {
            "ent": "math-arith",
            "aue": "raw",
        }

    def imgRead(self, path):
        with open(path, 'rb') as fo:
            return fo.read()

    def hashlib_256(self, res):
        m = hashlib.sha256(bytes(res.encode(encoding='utf-8'))).digest()
        result = "SHA-256=" + base64.b64encode(m).decode(encoding='utf-8')
        return result

    def httpdate(self, dt):
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                 "Oct", "Nov", "Dec"][dt.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month,
                                                        dt.year, dt.hour, dt.minute, dt.second)

    def generateSignature(self, digest):
        signatureStr = "host: " + self.Host + "\n"
        signatureStr += "date: " + self.Date + "\n"
        signatureStr += self.HttpMethod + " " + self.RequestUri \
                        + " " + self.HttpProto + "\n"
        signatureStr += "digest: " + digest
        signature = hmac.new(bytes(self.Secret.encode(encoding='utf-8')),
                             bytes(signatureStr.encode(encoding='utf-8')),
                             digestmod=hashlib.sha256).digest()
        result = base64.b64encode(signature)
        return result.decode(encoding='utf-8')

    def init_header(self, data):
        digest = self.hashlib_256(data)
        sign = self.generateSignature(digest)
        authHeader = 'api_key="%s", algorithm="%s", ' \
                     'headers="host date request-line digest", ' \
                     'signature="%s"' \
                     % (self.APIKey, self.Algorithm, sign)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Method": "POST",
            "Host": self.Host,
            "Date": self.Date,
            "Digest": digest,
            "Authorization": authHeader
        }
        return headers

    def get_body(self):
        audioData = self.imgRead((self.AudioPath))
        content = base64.b64encode(audioData).decode(encoding='utf-8')
        postdata = {
            "common": {"app_id": self.APPID},
            "business": self.BusinessArgs,
            "data": {
                "image": content,
            }
        }
        body = json.dumps(postdata)
        return body

    def call_url(self):
        if self.APPID == '' or self.APIKey == '' or self.Secret == '':
            print('Appid 或APIKey 或APISecret 为空！请打开demo代码，填写相关信息。')
        else:
            code = 0
            body = self.get_body()
            headers = self.init_header(body)
            response = requests.post(self.url, data=body, headers=headers, timeout=8)
            status_code = response.status_code
            if status_code != 200:
                print("Http请求失败，状态码：" + str(status_code) + "，错误信息：" + response.text)
                print("请根据错误信息检查代码，接口文档：https://www.xfyun.cn/doc/words/photo-calculate-recg/API.html")
            else:
                respData = json.loads(response.text)
                # print(respData)  # 打印原始API返回结果
                code = str(respData["code"])
                if code != '0':
                    print("请前往https://www.xfyun.cn/document/error-code?code=" + code + "查询解决办法")
                else:
                    self.mark_image(respData)

    def mark_image(self, respData):
        # 读取图片
        image = Image.open(self.AudioPath)
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", size=20)  # 选择字体和大小

        for line in respData['data']['ITRResult']['multi_line_info']['imp_line_info']:
            x1 = line['imp_line_rect']['left_up_point_x']
            y1 = line['imp_line_rect']['left_up_point_y']
            x2 = line['imp_line_rect']['right_down_point_x']
            y2 = line['imp_line_rect']['right_down_point_y']

            # 判断对错并使用不同颜色绘制矩形框
            if line['total_score'] == 1:
                draw.rectangle(((x1, y1), (x2, y2)), outline='green', width=2)  # 正确：绿色
            else:
                draw.rectangle(((x1, y1), (x2, y2)), outline='red', width=2)    # 错误：红色

        # 展示图片
        image.show()
        image.save("itr/result.jpg")  # 保存图片



def math_eq_correction():
    # 图片默认在itr文件夹下，文件名为itr.jpg
    host = "rest-api.xfyun.cn"
    gClass = get_result(host)
    gClass.call_url()