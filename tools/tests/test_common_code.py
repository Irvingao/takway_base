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


# 示例文本
# text = "你好，世界！今天天气怎么样？希望你有一个美好的一天。"
text = "你好，世界！今天天气"
sentences, punctuation_list = split_chinese_text(text)

print("断句结果:", sentences)
print("标点符号列表:", punctuation_list)

text = "你"
patch_text = split_chinese_text(text, return_patch=True)
print("补全后的文本:", patch_text)
