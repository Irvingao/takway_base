import pyaudio
import wave

# #####################################################
# Set chunk size of 1024 samples per data frame
chunk = 1024


# 16 bits per sample
sample_format = pyaudio.paInt16
channels = 1

# Record at 16000 samples per second
sample_rate = 16000

device_index = 2  # Index of the output device
# #####################################################

filename = f"out_{channels}.wav"
# Open the audio file
af = wave.open(filename, 'rb')

# Create an interface to PortAudio
pa = pyaudio.PyAudio()

# Get the sample width in bytes
sample_width = af.getsampwidth()

# Open a stream to play the audio
stream = pa.open(format=sample_format,
                channels=channels,
                rate=sample_rate,
                output=True,
                output_device_index=device_index)  # Specify the output device index

# Read data in chunks and play the sound

params = af.getparams()
rd_data = af.readframes(params.nframes)
stream.write(rd_data)

print("playing...")

# Close and terminate the stream
stream.stop_stream()
stream.close()
pa.terminate()

# Close the audio file
af.close()