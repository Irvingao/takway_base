def getText(text, role,content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = f"{content}"
    text.append(jsoncon)
    return text

def getlength(text):
    length = 0
    for content in text:
        temp = content["content"]
        leng = len(temp)
        length += leng
    return length

def checklen(text):
    while (getlength(text) > 8000):
        del text[0]
    return text

def text_process(word_list):
    irregular_str = ' '.join(word_list)
    # 去掉字符串中的方括号和单引号
    clean_str = irregular_str.replace("[", "").replace("]", "").replace("'", "").replace(" ", "")
    return clean_str


###################### roly-play ###########################
import json
def get_game(game_json_path="game.json"):
    with open(game_json_path, 'r',encoding="UTF-8") as f:
        game_data = json.load(f)
    return game_data

def get_user(user_json_path="user.json"):
    with open(user_json_path, 'r',encoding="UTF-8") as f:
        user_data = json.load(f)
    return user_data

def generate_sys_prompt(text, game_data):
    global chatbot
    max_token_limit = 8000
    chat_history = ""
    token_count = 0

    goal = game_data.get('Goal', '')
    rules = game_data.get('Rules', '')
    output_format = game_data.get('Output_format', '')
    example_conversation = game_data.get('Example_Conversation', '')

    content = f"""# 回合制游戏\n我们在玩一个问答形式的回合制游戏。\n\n## 游戏目标\n{goal}\n\n## 游戏规则\n{rules}\n\n## 输出格式\n{output_format}\n\n## 示例对话\n{example_conversation}"""
    print(content)
    
    jsoncon = {}
    jsoncon["role"] = "system"
    jsoncon["content"] = content
    text.append(jsoncon)
    return text

def getgameText(text, role, content):
    jsoncon = {}
    jsoncon["role"] = role
    jsoncon["content"] = f"""{content}"""
    # jsoncon["content"] = f"""对象的生气原因是：{content}，请按照输出格式输出："""
    text.append(jsoncon)
    return text

def clearPromptText(text, content):
    text[-1]["content"] = content
    return text
# 女朋友吃胖了，你说让他减肥，然后她就生气了
