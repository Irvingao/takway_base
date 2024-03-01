import os
import re

# 排序函数
def extract_number(file_name):
    # 使用正则表达式提取文件名中的数字
    match = re.search(r'\d+', file_name)
    return int(match.group()) if match else 0

def get_mp4_files(root_dir):
    mp4_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.mp4'):
                mp4_files.append(os.path.join(root, file))
            # 根据提取的数字对文件名进行排序
        mp4_files = sorted(mp4_files, key=extract_number)
    return mp4_files

# 使用方法示例
root_dir = 'ResizedEmoji/兴奋'  # 将此路径替换为Emoji文件夹的实际路径
mp4_files_list = get_mp4_files(root_dir)
print(mp4_files_list)
