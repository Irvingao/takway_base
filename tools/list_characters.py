from vits import tts_model_init

hps_ms, device, speakers, net_g_ms, limitation = tts_model_init(device='cpu')

for i, character in enumerate(speakers):
    print(f"{i}: {character}")