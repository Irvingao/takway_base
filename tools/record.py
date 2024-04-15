from takway.audio_utils import BaseRecorder

if __name__ == '__main__':
    recorder = BaseRecorder()
    recorder.record("my_recording.wav", # save as my_recording.wav
                    duration=5) # record for 5 seconds
    
    '''
    from takway.audio_utils import HDRecorder

    recorder = HDRecorder(filename="hd_recording.wav")
    # recorder = HDRecorder(filename="hd_recording.pcm")

    recorder.record_hardware(return_type='io')
    '''
    