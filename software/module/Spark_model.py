import sparkapi

appid = "f3767b32"
api_key = "6eff91ce581e5cb276db75ba91552377"
api_secret = "NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5"
domain = "generalv3.5"





Spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"  # Max服务地址


# 初始上下文内容，当前可传system、user、assistant 等角色
text = []


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
    while (getlength(text) > 8000):
        del text[0]
    return text




def spark_chat():
    """
    Spark聊天机器人
    :return:
    """
    answer = []  # 答案列表,answer[-1]为最新答案
    while (1):
        Input = input()
        question = checklen(getText("user", Input))
        sparkapi.answer = ""
        sparkapi.main(appid, api_key, api_secret, Spark_url, domain, question)
        answer.append(sparkapi.answer)
        getText("assistant", sparkapi.answer)







