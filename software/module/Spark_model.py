import sparkapi

appid = "f3767b32"
api_key = "6eff91ce581e5cb276db75ba91552377"
api_secret = "NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5"
domain = "generalv3.5"

Spark_url = "wss://spark-api.xf-yun.com/v3.5/chat"  # Max服务地址


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


# 初始上下文内容，当前可传system、user、assistant 等角色
text = []
answers = []  # 答案列表,answer[-1]为最新答案


def spark_chat(message):
    """
    Spark聊天机器人
    :return:
    """
    Input = message
    question = checklen(getText("user", Input))
    sparkapi.answer = ""
    sparkapi.main(appid, api_key, api_secret, Spark_url, domain, question)
    answers.append(sparkapi.answer)
    getText("assistant", sparkapi.answer)
    return answers[-1]


def shutdown_cleanup():
    """
    清理函数，用于清空text和answer
    """
    text.clear()
    answers.clear()

