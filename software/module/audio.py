import pyaudio
import wave
import audioop
import time

# 音频参数
FORMAT = pyaudio.paInt16  # 音频格式（16位 PCM）
CHANNELS = 1  # 声道数
RATE = 16000  # 采样率
CHUNK = 1024  # 每次读取的音频流长度（每个缓冲区的帧数）
SILENCE_THRESHOLD = 500  # 静音阈值
SILENCE_DURATION = 2  # 静音持续时间，单位秒
WAVE_OUTPUT_FILENAME = "audio/audio.pcm"  # 输出文件名


def Record_Audio():
    # 初始化 PyAudio
    p = pyaudio.PyAudio()

    # 打开音频流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    # 开始录音
    frames = []
    silent_chunks = 0
    silent_time = 0
    recording = True

    while recording:
        data = stream.read(CHUNK)
        frames.append(data)
        # 计算当前音频块的振幅
        amplitude = audioop.rms(data, 2)

        # 检测是否为静音
        if amplitude < SILENCE_THRESHOLD:
            if silent_chunks == 0:
                silent_start_time = time.time()  # 开始静音计时
            silent_chunks += 1
            # 计算静音持续的时间
            silent_time = time.time() - silent_start_time
            if silent_time > SILENCE_DURATION:
                print("检测到静音，停止录音。")
                recording = False
        else:
            silent_chunks = 0

    # 停止和关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()

    # 保存 PCM 文件
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return "文件已保存"
