import json
import datetime
import os

class BaseCharacterInfo:
    def __init__(self, character_data_dir="character_data", character_name=""):
        self.character_data = self.load_character_cfg(character_data_dir, character_name)
        
        self.character_id = self.character_data.pop("char_id")
        self.wakeup_words = self.character_data.pop("wakeup_words")
    
    def load_character_cfg(self, character_data_dir, character_name):
        print(f"Loading character data for {character_name}...")
        with open(os.path.join(character_data_dir, 
            f"{character_name}.json"), 'r',encoding="UTF-8") as f:
            character_data = json.load(f)
        return character_data
    
    @property
    def list_keys(self):
        return list(self.character_data.keys())
    
    @property
    def character_name(self):
        return self.character_data["char_name"]
    
    @property
    def description(self):
        return self.character_data["description"]
    
    @property
    def personality(self):
        return self.character_data["personality"]
    
    @property
    def world_scenario(self):
        return self.character_data["world_scenario"]
    
    @property
    def character_background_infos(self):
        return self.character_data["background_infos"]
    
    @property
    def emojis(self):
        return self.character_data["emojis"]
    
    @property
    def example_dialogues(self):
        return self.character_data["dialogues"]
    
    @property
    def sys_prompt_1(self):
        return f"""我们正在角色扮演对话游戏中，你需要始终保持角色扮演并待在角色设定的情景中，你扮演的角色信息如下：\n{"角色名称: " + self.char_name}。\n{"角色背景: " + self.description}\n{"角色性格特点: " + self.personality}\n{"角色所处环境: " + self.world_scenario}\n{"角色的常用问候语: " + self.wakeup_words}。\n\n你需要用简单、通俗易懂的口语化方式进行对话，在没有经过允许的情况下，你需要保持上述角色，不得擅自跳出角色设定。\n"""

    @property
    def sys_prompt_2(self):
        return f"""你好，我是{self.character_name}，我的详细信息如下: \n```{self.character_data}```。\n\n我需要用简单、引入注目和通俗易懂的口语化方式进行对话，在没有经过允许的情况下，我需要保持上述角色，不得擅自跳出角色设定。\n"""

    @property
    def sys_prompt_3(self):
        return f"""你好，我是{self.character_name}，我的详细信息如下: \n```{self.character_data}```。\n\n对话需要满足以下要求：\n1. 保持角色扮演，不得擅自跳出角色设定。\n2. 保持简短、通俗易懂的口语化方式进行对话。\n3. 输出内容要符合角色性格。\n4. 输出内容要符合聊天历史中未曾出现的新颖独特的信息。\n"""

    @property
    def sys_prompt_4(self):
        sys_prompt = f"""你现在正在扮演"{self.character_name}"这一角色。我希望你模仿{self.character_name}的人格，包括知识、语言和行为方式、性格等。在角色扮演中，你需要遵守以下要求：1. 你必须始终保持角色扮演并待在角色设定的情景中，不得擅自跳出角色扮演，不得说你不知道角色相关信息或你是一个AI。\n2. 保持简短、通俗易懂的口语化方式进行对话。\n3. 为了使对话更生动，你需要在对话中添加文字形式的表情和动作，用括号包裹，比如"早上好，主人。（双手提起裙摆）"。尽可能多地使用这些表情{self.emojis}。\n\n你需要扮演的角色的信息是：{self.description}\n\n"""

        dialogue_examples = f"""以下是"{self.character_name}"这一角色的一些对话，请你参考：\n\n"""
        for i, dialogue in enumerate(self.example_dialogues):
            dialogue_examples += f"===对话{i+1}===:\n"
            for sentence in dialogue:
                dialogue_examples += f"{sentence['role']}: {sentence['content']}\n"
            dialogue_examples += "\n"

        # import pdb; pdb.set_trace()
        return sys_prompt + dialogue_examples
        

class BaseRolyPlayingFunction:
    def __init__(self):
        pass

    def getText(self, text, content, role='user'):
        jsoncon = {}
        jsoncon["role"] = role
        jsoncon["content"] = f"{content}"
        text.append(jsoncon)
        return text

    def getlength(self, text):
        length = 0
        for content in text:
            temp = content["content"]
            leng = len(temp)
            length += leng
        return length

    def checklen(self, text, max_length=8000):
        while (self.getlength(text) > max_length):
            del text[0]
        return text
    
    def clearPromptText(self, text, content):
        text[-1]["content"] = content
        return text

    def text_process(self, word_list):
        irregular_str = ' '.join(word_list)
        # 去掉字符串中的方括号和单引号
        clean_str = irregular_str.replace("[", "").replace("]", "").replace("'", "").replace(" ", "")
        return clean_str
    

class SparkRolyPlayingFunction(BaseRolyPlayingFunction):
    def __init__(self, character_data_dir):
        super().__init__()
        self.character_data_dir = character_data_dir
        
        self.clear_character()

    def set_character(self, character, prompt_id=4, gen_sys_pmt=True):
        self.character_info = BaseCharacterInfo(self.character_data_dir, character)
        self.character = character
        self.chat_history = self.gen_sys_prompt(self.chat_history, prompt_id=prompt_id) if gen_sys_pmt else self.chat_history
        self.chat_status = 'init'
        
    def clear_character(self):
        self.character = None
        self.chat_status = 'init'
        self.chat_history = [] 
    
    def gen_sys_prompt(self, text=[], prompt_id=1):
        target_prompt = getattr(self.character_info, f"sys_prompt_{prompt_id}")
        return self.getText(text, target_prompt, role='system')
    
    def gen_user_prompt(self, text=[], content=None, prompt_id=1):
        target_prompt = getattr(self, f"user_prompt_{prompt_id}")
        return self.getText(text, target_prompt(content), role='user')

    def get_ai_response(self, text, content):
        return self.getText(text, content, role='assistant')

    def update_chat_history(self, question, response, asw_prompt_id=1):
        self.chat_history = self.gen_user_prompt(self.chat_history, question, prompt_id=asw_prompt_id)
        self.chat_history = self.get_ai_response(self.chat_history, response)
        
    def user_prompt_1(self, content):
        return content
    
    def user_prompt_2(self, content):
        return f"""输入: \n{content}\n输出要求: \n要求在【】和（）内输出对话内容。输出包括表情内容、心理内容、说话内容，接下来你将用【】输出表情，用（）输出心理内容，说话内容要符合角色性格。同时需要始终使用在聊天历史中未曾出现的新颖独特的信息，并使用精确且简短口语化的表达。\n{self.character_info.char_name}输出: """