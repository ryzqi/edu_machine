from fastapi import FastAPI
from pydantic import BaseModel
from universal_character_recognition import ocr
from TextCorrection import text_correction
from Mathematical_equation_correction import math_eq_correction
from Voice_Review import voice_review
from mp3_to_pcm import mp3_to_pcm
from Spark_model import spark_chat, shutdown_cleanup
from object_recognition import object_recognition, shutdown_cleanup_object_recognition

app = FastAPI()


class ObjectRecognitionRequest(BaseModel):
    message: str
    image_path: str | None = None



class ChatMessage(BaseModel):
    message: str


class TextCorrectionRequest(BaseModel):
    text: str


class OcrImageRequest(BaseModel):
    image_path: str


class VoiceReviewRequest(BaseModel):
    ENT: str  # 中文：cn_vip， 英文：en_vip
    CATEGORY: str  # 中文题型：read_syllable（单字朗读，汉语专有）read_word（词语朗读）
    # read_sentence（句子朗读）read_chapter(篇章朗读)
    # 英文题型：read_word（词语朗读）read_sentence（句子朗读）read_chapter(篇章朗读)
    # simple_expression（英文情景反应）
    TEXT: str  # 待评测语音文本
    AudioFile: str  # 待评测语音文件路径


class MP3Request(BaseModel):
    AudioFile: str  # 语音文件路径


@app.get("/数学算式批改")
async def math_eq_correction_api():
    # 默认图片路径为"itr/itr.jpg",到时直接将图片保存在如上路径即可
    # 返回的是保存的图片路径
    return math_eq_correction()


@app.post("/语文文本批改")
async def text_correction_api(text: TextCorrectionRequest):
    result = text_correction(text.text)
    return {"result": result}


@app.post("/文字扫描")
async def Ocr(image_path: OcrImageRequest):
    result = ocr(image_path.image_path)
    return {"result": result}


@app.post("/语音评测")
async def voice_review_api(request: VoiceReviewRequest):
    result = voice_review(request.ENT, request.CATEGORY, request.TEXT, request.AudioFile)
    return {"result": result}


@app.post("/MP3转PCM")
async def mp3_to_pcm_api(request: MP3Request):
    result = mp3_to_pcm(request.AudioFile)  # 路径
    return {"result": result}


@app.post("/Spark对话")
async def spark_chat_api(request: ChatMessage):
    result = spark_chat(request.message)
    return {"result": result}


@app.get("/shutdown")
def shutdown_event():
    shutdown_cleanup()
    return {"message": "清理对话缓存成功"}


@app.post("/对象识别")
async def object_recognition_api(request: ObjectRecognitionRequest):
    result = object_recognition(request.message, request.image_path)
    return {"result": result}


@app.get("/shutdown_object_recognition")
def shutdown_object_recognition_event():
    shutdown_cleanup_object_recognition()
    return {"message": "清理对象识别缓存成功"}

