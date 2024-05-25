
from typing import Optional, Any

from sparkai.core.callbacks import BaseCallbackHandler
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
try:
    from dotenv import load_dotenv
except ImportError:
    raise RuntimeError('Python environment for SPARK AI is not completely set up: required package "python-dotenv" is missing.') from None

load_dotenv()


class MyHandler(BaseCallbackHandler):
    def __init__(self, color: Optional[str] = None) -> None:
        self.color = color

    def on_llm_new_token(self, token: str, *, chunk: None, **kwargs: Any, ):
        print(token)


def test_stream():

    spark = ChatSparkLLM(
        spark_api_url="wss://spark-api.xf-yun.com/v3.5/chat",
        spark_app_id="f3767b32",
        spark_api_key="6eff91ce581e5cb276db75ba91552377",
        spark_api_secret="NGRkZWYwOGFlYmRmYmVjODQxYWJkNjE5",
        spark_llm_domain="generalv3.5",
        streaming=True,
    )
    messages = [
                ChatMessage(
                        role="user",
                        content='你好'

    )]
    handler = MyHandler()
    a = spark.generate([messages], callbacks=[handler])
    print(a)


test_stream()