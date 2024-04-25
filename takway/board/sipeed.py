import sys
import warnings
import threading
import time
from collections import deque

from takway.board.base_hd import BaseHardware

if "gpiod" in sys.modules:
    # sipeed MaixSense V329
    import gpiod as gpio
else:
    # 如果所有库都不存在，执行默认操作或抛出异常
    # raise ImportError("gpiod package is not available.")
    warnings.warn("gpiod package is not available.")

class V329(BaseHardware):
    def __init__(self, hd_trigger='button', hd_detect_threshold=50):
        super().__init__(hd_trigger, hd_detect_threshold)
        self.button = self.button_init()
        
        self.init_hd_thread()
    
    def button_init(self):
        PH_BASE = (8-1)*32 #PH

        gpiochip1 = gpio.chip("gpiochip1")
        button = gpiochip1.get_line((PH_BASE+5))
        config = gpio.line_request()
        config.request_type = gpio.line_request.DIRECTION_INPUT
        config.flags = gpio.line_request.FLAG_BIAS_PULL_UP
        button.request(config)
        return button

    @property
    def button_status(self):
        return True if self.button.get_value() == 1 else False
        
    def hd_detection_loop(self):
        self.shared_hd_status = False
        button_value_list = deque(maxlen=self.hd_detect_threshold)
        
        while True:
            if len(button_value_list) > button_value_list.maxlen:
                button_value_list.popleft()
            button_value_list.append(self.button_status)
            # 记录50个值，如果连续50个值都是True，则认为按钮被按下
            if button_value_list.count(True) == button_value_list.maxlen:
                with self.hd_lock:
                    self.shared_hd_status = True
            # 记录50个值，如果连续50个值都是False，则认为按钮被松开
            if button_value_list.count(False) == button_value_list.maxlen:
                with self.hd_lock:
                    self.shared_hd_status = False
    
    


