import wave 
# 读取wave文件，并打印采样率、量化位数、声道数
# 读取wave文件，并打印data长度
with wave.open('output_1708083097.9604511.wav', 'rb') as f:
    data = f.readframes(f.getnframes())
    print(len(data))
    print(type(data))
    nchannels, sampwidth, framerate, nframes, comptype, compname = f.getparams()
    print(framerate, sampwidth, nchannels)
    
