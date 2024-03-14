from takway.llm.openllm_api import OpenLLMAPI

def terminal_chat(api_key="xxx", 
                  base_url="http://10.10.42.227:8000/v1", 
                  model="internlm2-chat-1_8b", 
                  temperature=0.7, 
                  **kwargs):
    open_llm_api = OpenLLMAPI(api_key=api_key, base_url=base_url, model=model, stream=False)
    
    sys_prompt = "WRITE YOUR SYSTEM PROMPT HERE"
    # add system prompt to chat history
    chat_history = open_llm_api.creat_sys_prompt(prompt=sys_prompt, chat_history=[])
    
    while True:
        prompt = input("user: ")
        if prompt == "exit":
            break
        chat_history = open_llm_api.create_chat_prompt(prompt, chat_history)
        response = open_llm_api.get_completion(chat_history, temperature=temperature)
        open_llm_api.update_ai_prompt(response.choices[0].message.content, chat_history)
        print("AI: " + response.choices[0].message.content)
        
        
if __name__ == '__main__':
    terminal_chat()