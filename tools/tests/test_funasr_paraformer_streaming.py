from funasr import AutoModel

chunk_size = [0, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
chunk_size = [0, 8, 4] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
encoder_chunk_look_back = 4 #number of chunks to lookback for encoder self-attention
decoder_chunk_look_back = 1 #number of encoder chunks to lookback for decoder cross-attention

model = AutoModel(model="paraformer-zh-streaming")

import soundfile
import os

# wav_file = "当然是因为托尼带水啦，嘻嘻。看你这么菜，那我问你一个：有一根牙签走在马路上，看见一只刺猬，于是他停下来说什么？.wav"
wav_file = "web_request_test_audio.wav"

speech, sample_rate = soundfile.read(wav_file)
chunk_stride = chunk_size[1] * 960 # 600ms

cache = {}
total_chunk_num = int(len((speech)-1)/chunk_stride+1)
print(f"chunk_size: {chunk_size}, chunk_stride: {chunk_stride}, total_chunk_num: {total_chunk_num}")
import time
print("Start to recognize speech"); t_bgn = time.time()
for i in range(total_chunk_num):
    t_stamp = time.time()
    speech_chunk = speech[i*chunk_stride:(i+1)*chunk_stride]
    is_final = i == total_chunk_num - 1
    res = model.generate(input=speech_chunk, cache=cache, is_final=is_final, chunk_size=chunk_size, encoder_chunk_look_back=encoder_chunk_look_back, decoder_chunk_look_back=decoder_chunk_look_back)
    print(f"each chunk time: {time.time()-t_stamp}")
    # print(f"cache: {cache}")
    print(res)
print(f"Total time: {time.time()-t_bgn}")