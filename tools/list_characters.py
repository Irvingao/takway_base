from takway.vits_utils import tts_model_init

hps_ms, device, speakers = tts_model_init(device='cuda')

for i, character in enumerate(speakers):
    print(f"{i}: {character}")