EMO = '静态'
# EMO = '愤怒'

import time
import av
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
        print(root)
        for file in files:
            if file.endswith('.mp4'):
                mp4_files.append(os.path.join(root, file))
            # 根据提取的数字对文件名进行排序
        mp4_files = sorted(mp4_files, key=extract_number)
    return mp4_files

emo_time_dict = {
    '兴奋': 0.05,
    '愤怒': 0.01,
    '静态': 0.01,
}


t1 = time.time()
# 使用方法示例
# root_dir = 'ResizedEmoji/兴奋'  # 将此路径替换为Emoji文件夹的实际路径
# root_dir = 'ResizedEmoji/静态'  # 将此路径替换为Emoji文件夹的实际路径
root_dir = f'ResizedEmoji/{EMO}'  # 将此路径替换为Emoji文件夹的实际路径
video_paths = get_mp4_files(root_dir)
print(video_paths)


# 打开所有视频文件
containers = [av.open(path) for path in video_paths]
t2 = time.time(); print("open video time:", t2-t1)
video_streams = [container.streams.video[0] for container in containers]
t3 = time.time(); print("get video stream time:", t3-t2)


from maix import display, image
print("start display")
# while True:
for i, container in enumerate(containers):
    for frame in container.decode(video=0):
        img = image.load(bytes(frame.to_rgb().planes[0]), (video_streams[i].width, video_streams[i].height))
        display.show(img)
        time.sleep(emo_time_dict[EMO])  # 你可能需要根据视频的帧率调整这个延时
    time.sleep(1)  # 你可能需要根据视频的帧率调整这个延时
