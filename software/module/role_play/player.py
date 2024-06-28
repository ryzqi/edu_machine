import hashlib
import hmac
import base64
import json
import time
import requests

# ApiAuthAlgorithm这个类是为了对url鉴权的时候使用
class ApiAuthAlgorithm:
    MD5_TABLE = [
        '0', '1', '2', '3', '4', '5', '6', '7',
        '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'
    ]

    @staticmethod
    def get_signature(app_id, secret, ts):
        try:
            auth = ApiAuthAlgorithm.md5(app_id + str(ts))
            return ApiAuthAlgorithm.hmac_sha1_encrypt(auth, secret)
        except Exception as e:
            print(f"Error generating signature: {e}")
            return None

    @staticmethod
    def hmac_sha1_encrypt(encrypt_text, encrypt_key):
        try:
            data = bytes(encrypt_key, 'utf-8')
            secret_key = hmac.new(data, bytes(encrypt_text, 'utf-8'), hashlib.sha1)
            raw_hmac = secret_key.digest()
            return base64.b64encode(raw_hmac).decode('utf-8')
        except Exception as e:
            print(f"Error in hmac_sha1_encrypt: {e}")
            raise

    @staticmethod
    def md5(cipher_text):
        try:
            md = hashlib.md5()
            md.update(cipher_text.encode('utf-8'))
            md5_bytes = md.digest()
            md5_str = ''.join(
                [ApiAuthAlgorithm.MD5_TABLE[b >> 4 & 0xf] + ApiAuthAlgorithm.MD5_TABLE[b & 0xf] for b in md5_bytes])
            return md5_str
        except Exception as e:
            print(f"Error in md5: {e}")
            return None

# 这里if—register这个函数是用来判断用户是否注册
'''
methods：GET
request.get(url,headers)
输入
{
"appId":"";
"playername":"";
}
输出
{'success': True, 'code': 10000, 'message': '操作成功！', 'data': False, 'sid': '81cff6712ea340ff87ff41272b861068'}
'''
def if_register(url, app_id, secret, player_name):
    try:
        suffix_url = "/open/player/if-register"
        timestamp = int(time.time() * 1000)
        signature = ApiAuthAlgorithm.get_signature(app_id, secret, timestamp)

        if signature is None:
            print("Error generating signature")
            return

        full_url = f"{url}{suffix_url}?appId={app_id}&playerName={player_name}"
        headers = {
            "appId": app_id,
            "timestamp": str(timestamp),
            "signature": signature
        }

        response = requests.get(full_url, headers=headers)

        if response.status_code == 200:
            print(response.status_code)
            response_msg = response.json()
            print(response_msg)
            if response_msg.get("code") != 10000:
                raise Exception(f"查询失败，responseMsg = {response_msg}")
        else:
            print(f"Failed to retrieve data: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

# register创建的是玩家用户
#request中参数很多
def register(url,Appid,secret,playername,playertype,decription,senderIdentity):
    try:
        suffix_url = 'open/player/register'
        timestamp = int(time.time() * 1000)
        signature = ApiAuthAlgorithm.get_signature(Appid,secret,timestamp)
        data = {
            "appId":Appid,
            "playerName":playername,
            "playerType":playertype,
            "description":decription,
            "senderIdentity":senderIdentity
        }
        data = json.dumps(data)
        headers = {
            "appId": Appid,
            "timestamp": str(timestamp),
            "signature": signature
        }
        full_url = url + suffix_url
        response = requests.post(full_url, headers=headers,data=data)

        if response.status_code == 200:#这里的状态码是看请求是否发送到了
            response_msg = response.json()
            print(response_msg)
            if response_msg.get("code") != 10000:
                raise Exception(f"注册玩家失败，responseMsg = {response_msg}")
        else:
            print(f"Failed to register player: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

#编辑玩家账号
#有些数据可以不用输入即可完成修改，但是具体如何操作先不急
def modify(url,appid,secret,playerId,playerName,playerType,description,senderIdentity):
    try:
        suffix_url = "open/player/modify"
        timestamp = int(time.time() * 1000)
        signature = ApiAuthAlgorithm.get_signature(appid,secret,timestamp)
        full_url = url+suffix_url
        headers = {
            "appId": appid,
            "timestamp": str(timestamp),
            "signature": signature
        }
        data = {
                "appId": appid,
                "playerId": playerId,
                "playerName": playerName,
                "description":description,
                "playerType": playerType,
                "senderIdentity": senderIdentity
        }
        data = json.dumps(data)
        response = requests.post(full_url,headers=headers,data=data)
        if response.status_code == 200:  # 这里的状态码是看请求是否发送到了
            response_msg = response.json()
            print(response_msg)
            if response_msg.get("code") != 10000:#这里状态码返回10000为成功
                raise Exception(f"编辑玩家失败，responseMsg = {response_msg}")
        else:
            print(f"Failed to modify player: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

#删除玩家账户
def delete(url,appid,secret,playerId,playerName):
    try:
        suffix_url = 'open/player/delete'
        timestamp = int(time.time() * 1000)
        signature = ApiAuthAlgorithm.get_signature(appid, secret, timestamp)
        full_url = url + suffix_url
        headers = {
            "appId": appid,
            "timestamp": str(timestamp),
            "signature": signature
        }
        data = {
            "appId": appid,
            "playerId": playerId,
            "playerName": playerName,
        }
        data = json.dumps(data)
        response = requests.post(full_url, headers=headers, data=data)
        if response.status_code == 200:  # 这里的状态码是看请求是否发送到了
            response_msg = response.json()
            print(response_msg)
            if response_msg.get("code") != 10000:  # 这里状态码返回10000为成功
                raise Exception(f"删除玩家失败，responseMsg = {response_msg}")
        else:
            print(f"Failed to delete player: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

'''
plyer.py的作用就是注册角色、编辑角色、检验角色注册清理、删除角色

url='https://ai-character.xfyun.cn/api/'
appid = '7d21d663'
secret ='N2YyMjkxODgzMGYxZjg1YTNlMDAyYjQx'
playerId='000a794da51cbd2651e9284eb7b5f78b'
playerName='chu'
playerType='管理员'
description="管理员拥有最高权限"
senderIdentity="管理员"
register(url,appid,secret,playerName,playerType,description,senderIdentity)
#delete(url,appid,secret,playerId,playerName)
'''