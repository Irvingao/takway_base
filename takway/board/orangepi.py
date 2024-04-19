import keyboard
import time

from takway.board.base_hd import BaseHardware

import datetime
t=0
last_status = False

class OrangePi(BaseHardware):
    def __init__(self, hd_trigger='button', hd_detect_threshold=50):
        super().__init__(hd_trigger, hd_detect_threshold)
        
        self.BUTTON_PIN_blue = 8
        self.LED_PIN_blue = 5
        
        self.BUTTON_PIN_red = 6
        self.LED_PIN_red = 2
        
        self.button_init()
        
        self.init_hd_thread()
    
    def button_init(self):
        subprocess.run(["gpio", "mode", str(self.LED_PIN_red), "out"])
        subprocess.run(["gpio", "mode", str(self.BUTTON_PIN_red), "in"])
        
    @property
    def button_status(self):
        return self.shared_hd_status
        
    def hd_detection_loop(self):
        keyboard_status = False
        while True:
            '''
            keyboard_status = keyboard.is_pressed(self.keyboard_key)
            with self.hd_lock:
                self.shared_hd_status = keyboard_status
            '''
            self.shared_hd_status = True if subprocess.run(["gpio", "read", str(self.BUTTON_PIN_red)], capture_output=True, text=True).stdout.strip() == '0' else False
            
            global t, last_status
            if t%2 == 0 and not self.shared_hd_status and last_status:
                print(f"pres time: {datetime.datetime.now()}")
            last_status = self.shared_hd_status
            t+=1
    