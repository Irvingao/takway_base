import os
import struct
import wave
from datetime import datetime

import pvporcupine
from pvrecorder import PvRecorder


class PorcupineKeywordDetector:
    def __init__(self, access_key, keywords=None, keyword_paths=None, library_path=None, model_path=None, sensitivities=None, audio_device_index=-1, output_path=None):
        self.access_key = access_key
        self.keywords = keywords
        self.keyword_paths = keyword_paths
        self.library_path = library_path
        self.model_path = model_path
        self.sensitivities = sensitivities if sensitivities is not None else [0.5] * len(self.keyword_paths)
        self.audio_device_index = audio_device_index
        self.output_path = output_path
        self.porcupine = None
        self.recorder = None
        self.wav_file = None

        if len(self.keyword_paths) != len(self.sensitivities):
            raise ValueError('Number of keywords does not match the number of sensitivities.')

        self._init_porcupine()

    def _init_porcupine(self):
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                library_path=self.library_path,
                model_path=self.model_path,
                keyword_paths=self.keyword_paths,
                sensitivities=self.sensitivities)
        except pvporcupine.PorcupineError as e:
            print("Failed to initialize Porcupine:", e)
            raise e

    def start_detection(self):
        self.recorder = PvRecorder(frame_length=self.porcupine.frame_length, device_index=self.audio_device_index)
        self.recorder.start()

        if self.output_path is not None:
            self.wav_file = wave.open(self.output_path, "w")
            self.wav_file.setnchannels(1)
            self.wav_file.setsampwidth(2)
            self.wav_file.setframerate(16000)

        print('Listening ... (press Ctrl+C to exit)')
        self._run_detection_loop()

    def _run_detection_loop(self):
        try:
            while True:
                pcm = self.recorder.read()
                result = self.porcupine.process(pcm)

                if self.wav_file is not None:
                    self.wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

                if result >= 0:
                    print('[%s] Detected %s' % (str(datetime.now()), self.keywords[result]))
        except KeyboardInterrupt:
            print('Stopping ...')
        finally:
            self.stop_detection()

    def stop_detection(self):
        if self.recorder is not None:
            self.recorder.delete()
        if self.porcupine is not None:
            self.porcupine.delete()
        if self.wav_file is not None:
            self.wav_file.close()

    # You can add more methods here as needed, such as a method to list audio devices.

# Usage example
if __name__ == '__main__':
    detector = PorcupineKeywordDetector(access_key='hqNqw85hkJRXVjEevwpkreB8n8so3w9JPQ27qnCR5qTH8a3+XnkZTA==')
    detector.start_detection()
