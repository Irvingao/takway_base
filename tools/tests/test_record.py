import pyaudio
import wave

# #####################################################
# Record in chunks of 1024 samples
chunk = 1024

# 16 bits per sample
sample_format = pyaudio.paInt16
channels = 1

# Record at 16000 samples per second
sample_rate = 16000
seconds = 4
filename = f"out_{channels}.wav"
# Specify the index of the device you want to use
device_index = 2
# #####################################################

# Create an interface to PortAudio
pa = pyaudio.PyAudio()

# List available devices
print("Available devices:")
for i in range(pa.get_device_count()):
    dev = pa.get_device_info_by_index(i)
    print(f"ID: {dev['index']}, Name: {dev['name']}, Max Input Channels: {dev['maxInputChannels']}")

# Open a stream with the specified device
stream = pa.open(format=sample_format, channels=channels,
                 rate=sample_rate, input=True,
                 input_device_index=device_index, # Specify the device index here
                 frames_per_buffer=chunk)

print('Recording...')

# Initialize array that will be used for storing frames
frames = []

# Store data in chunks for the specified duration
for i in range(0, int(sample_rate / chunk * seconds)):
    data = stream.read(chunk, exception_on_overflow=False)
    frames.append(data)

# Stop and close the stream
stream.stop_stream()
stream.close()

# Terminate - PortAudio interface
pa.terminate()

print('Done !!!')

# Save the recorded data in a .wav format
with wave.open(filename, 'wb') as wf:
    wf.setnchannels(channels)
    wf.setsampwidth(pa.get_sample_size(sample_format))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))

