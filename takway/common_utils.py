
# ############################################################# #
# format table function
# ############################################################# #

def format_table(header, rows):
    # 计算列宽
    col_width = max(len(str(word)) for row in rows for word in row) + 2  # 最大单词长度 + 2 作为列宽
    # 打印表头
    print("".join(word.ljust(col_width) for word in header))
    # 打印分隔线
    print("".join("-" * col_width for _ in header))
    # 打印内容
    for row in rows:
        print("".join(str(word).ljust(col_width) for word in row))

# ############################################################# #
# encode and decode bytes and string
# ############################################################# #

import base64
def encode_bytes2str(data):
    # 将字节串编码为Base64
    if data is None:
        return None
    return base64.b64encode(data).decode('utf-8')

def decode_str2bytes(data):
    # 将Base64编码的字节串解码为字节串
    if data is None:
        return None
    return base64.b64decode(data.encode('utf-8'))

import re
def split_sentences(text: str):
    # 定义中文标点符号的正则表达式
    pattern = r'[\。\，\、\；\：\？\！\“\”\（\）\《\》]+'
    # 使用正则表达式分割字符串
    sentences = re.split(pattern, text)
    # 过滤掉空字符串
    sentences = [sentence for sentence in sentences if sentence]
    return sentences
'''
# 示例文本
text = "今天天气真好，我们去公园玩吧！你觉得怎么样？好的，那就这么定了。"
# 调用函数进行断句
sentences = split_sentences(text)

print(sentences)
'''

def split_chinese_text(text: str, return_patch=False):
    # 定义中文标点符号集合
    punctuations = set('。！？，；：、“”（）《》【】')
    # 初始化断句结果列表和标点符号列表
    sentences = []
    punctuation_list = []
    
    text_patch = []
    
    start = 0  # 断句开始位置
    for i, char in enumerate(text):
        if char in punctuations:
            # 如果当前字符是标点符号，则进行断句，并记录标点符号
            sentences.append(text[start:i+1])
            punctuation_list.append(char)
            start = i + 1  # 更新断句开始位置
    
    # 处理最后一句（如果最后一句后没有标点符号）
    if start < len(text):
        sentences.append(text[start:])
        
        
    if return_patch:
        if len(punctuation_list) == 0:
            return [text], False       # 有残留语句
        elif len(sentences) == len(punctuation_list):
            return [''.join(sentences)], True
        else:
            return [''.join(sentences[:-1]), sentences[-1]], True
    return sentences, punctuation_list
'''
# 示例文本
text = "你好，世界！今天天气怎么样？希望你有一个美好的一天。"
sentences, punctuation_list = split_chinese_text(text)

print("断句结果:", sentences)
print("标点符号列表:", punctuation_list)
'''

def remove_brackets_and_contents(text):
    # 正则表达式匹配任何括号及其内容
    pattern = r'$.*?$'
    # 使用sub函数替换匹配的文本为空字符串
    result = re.sub(pattern, '', text)
    return result