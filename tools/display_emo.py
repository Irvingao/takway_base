'''
# path_to_video = '240x240_兴奋_1进入姿势.mp4'
path_to_video = 'ResizedEmoji/兴奋/兴奋_2可循环动作.mp4'

import os

command = f"sudo mplayer {path_to_video} -vo fbdev2 < /dev/null > /dev/null 2>1 &"

# os.system('ffmpeg -i'+ path_to_video +'-vf "scale=240:-1" -vframes 1'+ path_to_video[:-4] + '_frame.png')
os.system(command)

mplayer -cache 8192 240x240_兴奋_1进入姿势.mp4 -nosound -vo fbdev2 < /dev/null > /dev/null 2>1 &

mplayer -cache 8192 240x240_兴奋_1进入姿势.mp4 -nosound --enable-fbdev
'''



import time
t1 = time.time()
import av
from maix import display, image

path_to_video = 'ResizedEmoji/兴奋/兴奋_2可循环动作.mp4'
container = av.open(path_to_video)
vi_stream = container.streams.video[0]

t2 = time.time(); print("open video time:", t2-t1)
for frame in container.decode(video=0):
    t3 = time.time()# ; print("decode frame time:", t3-t2)
    # frame.to_image().save('frame-%04d.jpg' % frame.index)
    img = image.load(bytes(frame.to_rgb().planes[0]), (vi_stream.width, vi_stream.height))
    display.show(img)
    t4 = time.time(); print("show frame time:", t4-t3)
    