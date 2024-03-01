import time
import av
import os
import copy
import random
import numpy as np
try:
    from maix import display, image
    print("import maix success.")
except:
    import cv2
    print("import cv2 success.")

class EmoVideoPlayer:
    def __init__(self, player='maixsense', emo_dir='ResizedEmoji'):
        assert player in ['maixsense', 'opencv'], "player must be'maixsense' or 'opencv'"
        self.player = player
        
        self.emo_list = ['兴奋', '愤怒', '静态', '不屑', '惊恐', '难过']
        
        self.emo_init(emo_dir)

    def emo_init(self, emo_dir):
        # 将此路径替换为Emoji文件夹的实际路径
        self.emo_av_dict = self.get_emo_av(emo_dir)
        self.emo_time_dict = {
            '兴奋': 0.00,
            '愤怒': 0.01,
            '静态': 0.01,
            '不屑': 0.01,
            '惊恐': 0.01,
            '难过': 0.01,
        }
        
    def get_emo_av(self, emo_dir):
        emo_av_dict = {emo: dict() for emo in self.emo_list}
        for emo in self.emo_list:
            emo_path = os.path.join(emo_dir, emo)
            for file in os.listdir(emo_path):
                if not os.path.isfile(os.path.join(emo_path, file)):
                    continue
                av_container = av.open(os.path.join(emo_path, file))
                if emo == '静态':
                    if "单次眨眼偶发" in file:
                        emo_av_dict[emo]['seldom_wink'] = av_container
                    if "快速双眨眼偶发" in file:
                        emo_av_dict[emo]['quick_wink'] = av_container
                else:
                    if "进入姿势" in file:
                        emo_av_dict[emo]['start'] = av_container
                    elif "可循环动作" in file:
                        emo_av_dict[emo]['loop'] = av_container
                    elif "回正" in file:
                        emo_av_dict[emo]['end'] = av_container
        self.av_info = emo_av_dict[emo]['loop'].streams.video[0]
        return emo_av_dict
    
    def get_emo_frames(self, emo_dir):
        emo_av_dict = {emo: dict() for emo in self.emo_list}
        for emo in self.emo_list:
            emo_path = os.path.join(emo_dir, emo)
            for file in os.listdir(emo_path):
                if not os.path.isfile(os.path.join(emo_path, file)):
                    continue
                av_container = av.open(os.path.join(emo_path, file))
                
                frame_list = []
                av_info = av_container.streams.video[0]
                for frame in av_container.decode(video=0):
                    if self.player =='maixsense':
                        img = image.load(bytes(frame.to_rgb().planes[0]), (av_info.width, av_info.height))
                    elif self.player == 'opencv':
                        img = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                    frame_list.append(img)
                # add to dict
                if emo == '静态':
                    if "单次眨眼偶发" in file:
                        emo_av_dict[emo]['seldom_wink'] = frame_list
                    if "快速双眨眼偶发" in file:
                        emo_av_dict[emo]['quick_wink'] = frame_list
                else:
                    if "进入姿势" in file:
                        emo_av_dict[emo]['start'] = frame_list
                    elif "可循环动作" in file:
                        emo_av_dict[emo]['loop'] = frame_list
                    elif "回正" in file:
                        emo_av_dict[emo]['end'] = frame_list
        return emo_av_dict
    
    def display_emo_frame(self, emo_name, stage='default'):
        emo_frame_list = self.emo_av_dict[emo_name][stage]
        emo_time = self.emo_time_dict[emo_name]
        for img in emo_frame_list:
            if self.player =='maixsense':
                display.show(img)
            elif self.player == 'opencv':
                cv2.imshow("video", img)
                cv2.waitKey(1)  # 你可能需要根据视频的帧率调整这个延时
            time.sleep(emo_time) 
        
    def display_emo(self, emo_name, stage='default'):
        if self.player =='maixsense':
            self.display_emo_maixsense(emo_name, stage)
        elif self.player == 'opencv':
            self.display_emo_opencv(emo_name, stage)
        
    def display_emo_maixsense(self, emo_name, stage):
        emo_container = self.emo_av_dict[emo_name][stage]
        emo_time = self.emo_time_dict[emo_name]
        for frame in emo_container.decode(video=0):
            img = image.load(bytes(frame.to_rgb().planes[0]), (self.av_info.width, self.av_info.height))
            display.show(img)
            time.sleep(emo_time) 
        emo_container.seek(0)  # 重置视频的读取位置
    
    def display_emo_opencv(self, emo_name, stage='default'):
        import cv2
        import numpy
        if stage == 'default':
            if emo_name == '静态':
                stage = 'quick_wink'
            else:
                stage = 'loop'
        emo_container = self.emo_av_dict[emo_name][stage]
        emo_time = self.emo_time_dict[emo_name]
        
        for frame in emo_container.decode(video=0):
            img = cv2.cvtColor(numpy.array(frame.to_image()), cv2.COLOR_RGB2BGR)
            cv2.imshow("video", img)
            time.sleep(emo_time) 
            cv2.waitKey(1)  # 你可能需要根据视频的帧率调整这个延时
        cv2.destroyAllWindows()
        emo_container.seek(0)  # 重置视频的读取位置
        
    def get_emo_status(self, answer):
        # `兴奋`, `愤怒`, `静态`, `不屑`, `惊 恐`, `难过`
        if any([emo in answer for emo in self.emo_list]):
            # 找出是answer中出现了哪个emo    
            emo_status = [emo for emo in self.emo_list if emo in answer][0]
            print(f"emo_status: {emo_status}")
        else:
            emo_status = '静态'
        return emo_status
    
    def random_wink(self):
        seed = random.randrange(0, 1000)
        if seed < 100:
            self.display_emo(emo_name='静态', stage='seldom_wink')
            # print("random wink")
    
    
    
if __name__ == '__main__':

    emo = EmoVideoPlayer()
    # emo.display_emo_opencv(emo_name='兴奋', stage='start')
    # emo.display_emo_opencv(emo_name='兴奋', stage='loop')
    # emo.display_emo_opencv(emo_name='兴奋', stage='loop')
    # emo.display_emo_opencv(emo_name='兴奋', stage='loop')
    # emo.display_emo_opencv(emo_name='兴奋', stage='end')
    emo.display_emo_opencv(emo_name='静态', stage='seldom_wink')
    emo.display_emo_opencv(emo_name='静态', stage='quick_wink')
    # emo.display_emo_opencv(emo_name='愤怒', stage='start')
    # emo.display_emo_opencv(emo_name='愤怒', stage='loop')
    # emo.display_emo_opencv(emo_name='愤怒', stage='end')
    # emo.display_emo_opencv(emo_name='静态', stage='seldom_wink')
    # emo.display_emo_opencv(emo_name='静态', stage='quick_wink')
    # emo.display_emo_opencv(emo_name='不屑', stage='start')
    # emo.display_emo_opencv(emo_name='不屑', stage='loop')
    # emo.display_emo_opencv(emo_name='不屑', stage='end')
    # emo.display_emo_opencv(emo_name='惊恐', stage='start')
    # emo.display_emo_opencv(emo_name='惊恐', stage='loop')
    # emo.display_emo_opencv(emo_name='惊恐', stage='end')
    # emo.display_emo_opencv(emo_name='难过', stage='start')
    # emo.display_emo_opencv(emo_name='难过', stage='loop')
    # emo.display_emo_opencv(emo_name='难过', stage='end')