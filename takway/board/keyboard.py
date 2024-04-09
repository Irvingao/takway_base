import keyboard
import time

from takway.board.base_hd import BaseHardware

class Keyboard(BaseHardware):
    def __init__(self, hd_trigger='keyboard', keyboard_key='space', hd_detect_threshold=50):
        super().__init__(hd_trigger, hd_detect_threshold)
        
        self.keyboard_key = keyboard_key
        self.init_hd_thread()
        
    def hd_detection_loop(self):
        keyboard_status = False
        while True:
            keyboard_status = keyboard.is_pressed(self.keyboard_key)
            with self.hd_lock:
                self.shared_hd_status = keyboard_status
            time.sleep(0.001)