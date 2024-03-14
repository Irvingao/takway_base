from openai import OpenAI

from takway.roleplay_utils import BaseRolyPlayingFunction

class OpenLLMAPI(BaseRolyPlayingFunction):
    def __init__(self, 
                 api_key="xxx", 
                 base_url="http://10.10.42.227:8000/v1",
                 model="internlm2-chat-1_8b", 
                 stream=True,
                 **kwargs):
        super().__init__()
        '''
        class for api-for-open-llm backend
        '''
        self.model = model
        self.stream = stream
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url)

    def creat_sys_prompt(self, prompt, chat_history):
        chat_history = self.getText(chat_history, prompt, role='system')
        return chat_history
    
    def create_chat_prompt(self, prompt, chat_history):
        assert isinstance(chat_history, list), f"chat_history should be a list, \
            but got {type(chat_history)}, content: {chat_history}"
        chat_history = self.getText(chat_history, prompt, role='user')
        return chat_history
    
    def update_ai_prompt(self, response_text, chat_history):
        chat_history = self.getText(chat_history, response_text, role='assistant')
        return chat_history

    def get_completion(self, 
                       chat_prompts, 
                       temperature=0.7, 
                       **kwargs):
        '''
        get completion from unified backend api
        
        Example usage:
        - stream=True:
            ```
            response = open_llm_api.get_completion(chat_prompts, temperature=temperature)
            for chunk in response:
                print(chunk.choices[0].delta.content)
                # print(chunk.choices[0].delta.content or "", end="")
            ```
        - stream=False:
            ```
            response = open_llm_api.get_completion(chat_prompts, temperature=temperature)
            print(response.choices[0].message.content)
            ```
        '''
        response = self.client.chat.completions.create(
            model=self.model,
            messages=chat_prompts,
            stream=self.stream,
            temperature=temperature,
            **kwargs
        )
        return response
    
    
        
if __name__ == '__main__':
    prompt = "你好，浦语！"
    api_key = "xxx"
    base_url = "http://10.10.42.227:8000/v1"
    model = "internlm2-chat-1_8b"
    stream = True
    temperature = 0.7
    chat_history = []
    open_llm_api = OpenLLMAPI(api_key=api_key, base_url=base_url, model=model, stream=stream)
    import time; t_bgn = time.time()
    chat_history = open_llm_api.create_chat_prompt(prompt, chat_history)
    response = open_llm_api.get_completion(chat_history, temperature=temperature)
    t_rsp = time.time(); print(f"response time: {(t_rsp - t_bgn)*1000:0.4f} ms")
    for chunk in response:
        # print(chunk.choices[0].delta.content or "", end="")
        print(chunk.choices[0].delta.content)
        t_cuk = time.time(); print(f"chunk time: {(t_cuk - t_rsp)*1000:0.4f} ms")
    