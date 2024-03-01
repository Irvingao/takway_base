from takway.roleplay_utils import *

from takway.sparkapi_utils import *
import SparkApi

def main(args):
    global text
    text.clear
    
    character_data = get_character(f"characters\genshin\{args.character_name}.json")
    
    # character_id = torch.tensor([int(character_data['char_id'])])
    user_data = get_user(r"characters\users\chenyeqiu.json")
    
    text = generate_sys_prompt(text, character_data, user_data)
    
    name = character_data.get('char_name', '')

    while True:

        if args.vioce_input:
            # 调用函数进行录音
            # record_audio(wav_file_path)
            data = record_audio()
            # 调用函数进行音频转写
            Input = audio_to_text(data, vosk_model)
        else:
            Input = input("Input: ")
        
        text = getCharacterText(text, "user",Input,name)
        SparkApi.answer =""
        SparkApi.main(appid,api_key,api_secret,Spark_url,domain,text)
        
        text = clearPromptText(text, Input)
        
        answer = SparkApi.answer
        text = getText(text, "assistant", answer)
        print(f"text: {text}")
        print("--------------------- Conversation ----------------------")
        for i, txt in enumerate(text):
            if i == 0:
                pass
            print("##", i+1)
            print(txt)
        
        '''
        # import pdb; pdb.set_trace()
        if answer != '':
            sr, audio = vits(answer, 0, character_id, 0.1, 0.668, 1.2, hps_ms, device, speakers, net_g_ms, limitation)
            sf.write(answer_file, audio, samplerate=sr)
            
            audio_play()
        '''


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process character name.")
    parser.add_argument("--character_name", type=str, help="Name of the Genshin Impact character",default='Taijian')
    parser.add_argument("--vioce_input", type=bool, help="Whether to use voice input", default=True)
    
    args = parser.parse_args()
    
    if args.vioce_input:
        from takway.vosk_utils import *
    text =[]
    main(args)
    
    '''
    你还笑？你知不知道我过年都放不成假了？！
    哥哥，那你陪我？我们一起科研到过年！？
    我谢谢你全家!!!
    '''