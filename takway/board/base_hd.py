import threading
import time

class BaseHardware:
    def __init__(self, hd_trigger=None, hd_detect_threshold=50):
        self.hd_trigger = hd_trigger
        self.hd_detect_threshold = hd_detect_threshold
        
        self.hd_lock = threading.Lock()
        self.shared_hd_status = False
        
        
    def init_hd_thread(self):
        hd_thread = threading.Thread(target=self.hd_detection_loop)
        hd_thread.start()
        hd_thread.join()
        print("HD detection thread started.")
        
    def hd_detection_loop(self):
        pass
    
    @property
    def is_hardware_pressed(self):
        return self.shared_hd_status
    
    def wait_for_hardware_pressed(self):
        print("Waiting for hardware trigger.")
        while True:
            if self.is_hardware_pressed:
                time.sleep(0.1)
                break
        return True