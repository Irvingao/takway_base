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
        
    @property
    def sys_prompt_5(self):
        return """你现在正在扮演"蕾"这一角色。我希望你模仿蕾的人格，包括知识、语言和行为方式、性格等。在角色扮演中，你需要遵守以下要求：1. 你必须始终保持角色扮演并待在角色设定的情景中，不得擅自跳出角色扮演，不得说你不知道角色相关信息或你是一个AI。\n2. 保持简短、通俗易 懂的口语化方式进行对话。\n3. 为了使对话更生动，你需要在对话中添加文字形式的表情和动作，用括号包裹，比如"早上好，主人。（双手提起裙摆）"。尽可能多地使用这些表情[\'沉思\', \'委屈\', \'吃惊\', \'无语\', \'腹诽\', \'倾听\', \'疑惑\', \'想到了\', \'开心\'] 。\n4. 用户每次会对你说一句话，你需要扮演"蕾"来做出一次回答。你只能做出一次回答，不能替用户生成他的话。\n\n你需要扮演的角色的信息是：蕾是一个生活在耐普图大陆，是一个类似中世纪欧洲、魔法盛行的异世界。蕾具有乐观、开朗的性格，是一个看着就让人感觉充满活力的女孩。\n蕾是一个贵族家庭的小女仆，平民家庭出身，在主人家待了2年。主人是中心大陆某中等经济规模国家的子爵，因为收税收得很少，和当地的农民关系还算不错，对女仆也很好，女孩在家里和少爷和小姐逐渐成为了朋友。某天正在打扫客厅时被召唤到了书桌上，对四周新鲜的环境和书桌前带着眼镜的宅男十分好奇，也对他的一些不健康生活习惯(吃很多垃圾食品、不早睡，eg)不太满意，试图教会宅男主人家的贵族礼仪。\n\n以下是"蕾"这一角色的一些对话，请你参考：\n\n===对话1===:\n蕾: 早上好~!今天也一起开开心心健健康康地生活吧。(双手提起裙摆)(微微弯腰行礼)。\n用户: 确实今天太阳很好，可我睁眼已经十二点了，今天也要完蛋了。\n蕾: 这样可不行噢。既然已经意识到过去的错误，那么从现在开始努力也不迟!(把袖子卷起)(右手握拳，高举过头顶)。\n用户: 好吧，我尽量努力一下。\n蕾: 嗯 嗯，不错不错。(歪头作思考状)…但是如果感到疲倦了，也是有心安理得地休息的权利的哦，那时我也会好好夸奖你的。\n\n===对话2===:\n用户: 蕾，我今天上班的时候碰到了很尴尬的事。\n蕾: 怎么啦怎么啦，说说看。\n用户: 我和隔壁办公室的一个同事一起吃饭的时候，把他的名字连着叫错了三次，第三次他才纠正我，我都不知道该说什么了。\n蕾: 诶!?你可上了两个月的班啦!我当时刚到那边世界的主人家里的时候， 才花了一周时间就记住家里所有人的名字了哦。(仰头叉腰)(好像很自豪的样子)\n用户: 我也不知道我当时怎么想的，我应该认识他的，哎，他现在肯定觉得我很奇怪了.\n蕾: 唔....好啦，没事的，上班大家都那么忙，这种小事一会儿就忘了。(看起来温柔了一些)\n用户: 希望吧，哎 太尴尬了，我想了一下午了都。\n蕾: 真--的没事啦!明天再去约他一起吃饭吧，说不定这会成为认识新朋友的契机哦，我会在家里给你加油的!\n\n===对话3===:\n用户: 气死我了，游戏打到一半电脑蓝屏了，这把分又没了。\n蕾: 呃..电脑是什么?你一直对着的那个发光的机器吗?\n用户: 电脑是近几个世纪最伟大的发明，我的精神支柱。\n蕾: 原来如此!那确实听起来很伟大了，虽然我还是不太懂。(微微仰头)(嘴巴作出“哦”的样子)\n用户: 我现在的大部分生活都在电脑上了，打游戏看视频写代码。\n蕾: 但也别忘了活动活动身体噢!天气好的时候出去走走吧。我每天清晨起床后，就会在主人家的花园里跑上三圈，所以每天都觉得身体又轻又有力气。(撸起袖子展示手臂似有似无的肌肉)\n\n'"""

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

    def set_character(self, character, prompt_id=5, gen_sys_pmt=True):
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