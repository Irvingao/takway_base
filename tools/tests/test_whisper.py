from faster_whisper import WhisperModel

# model_size = "whisper-tiny-zh-ct2"
model_size = "whisper-tiny-zh-ct2-int8"

# Run on GPU with FP16
model = WhisperModel(model_size, device="cuda", compute_type="float16")
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, info = model.transcribe("当然是因为托尼带水啦，嘻嘻。看你这么菜，那我问你一个：有一根牙签走在马路上，看见一只刺猬，于是他停下来说什么？.wav", beam_size=5, language='zh')

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))