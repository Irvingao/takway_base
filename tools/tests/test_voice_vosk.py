#!/usr/bin/env python3

import pyaudio
import wave
import keyboard
import json
from vosk import Model, KaldiRecognizer, SetLogLevel

def record_audio(filename):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []
    recording = False

    print("Press SPACE to start recording...")
    keyboard.wait("space")
    print("Recording started.")

    while True:
        if keyboard.is_pressed("space"):
            if not recording:
                recording = True
                print("Recording...")
        else:
            if recording:
                recording = False
                print("Recording stopped.")
                break

        if recording:
            data = stream.read(CHUNK)
            frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(f"Audio saved as {filename}.")


def audio_to_text(filename, model):
    wf = wave.open(filename, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("Audio file must be WAV format mono PCM.")
        sys.exit(1)

    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)
    rec.SetPartialWords(True)

    text = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            print("xxxxxxxxxxxxx")
            print(res['text'])
            text.append(res['text'])
            print("xxxxxxxxxxxxx")

    text.append(json.loads(rec.FinalResult())['text'])
    return text




def main():
    wav_file_path = "recording.wav"

    # You can set log level to -1 to disable debug messages
    SetLogLevel(0)

    model = Model(model_path="vosk-model-small-cn-0.22")

    # 调用函数进行录音
    record_audio(wav_file_path)

    # 调用函数进行音频转写
    result = audio_to_text(wav_file_path)

    print("-------------")
    print(result)


if __name__ == "__main__":
    main()