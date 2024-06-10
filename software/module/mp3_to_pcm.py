import soundfile as sf


def mp3_to_pcm(mp3_file):
    # 读取MP3文件
    data, sample_rate = sf.read(mp3_file, dtype='int16')
    # 写入PCM文件
    sf.write('soundfile/output.pcm', data, sample_rate, format='RAW', subtype='PCM_16')
    return 'soundfile/output.pcm'




