from takway.board.base_hd import BaseHardware
import subprocess
import datetime
t=0
last_status = False

class OrangePi(BaseHardware):
    def __init__(self, hd_trigger='button', hd_detect_threshold=50):
        super().__init__(hd_trigger, hd_detect_threshold)
        
        self.BUTTON_PIN_red = 6
        self.LED_PIN_red = 2
        
        self.BUTTON_PIN_blue = 8
        self.LED_PIN_blue = 5
        
        self.shared_hd_status_2 = False
        
        self.button_init()
        self.init_hd_thread()
    
    def button_init(self):
        subprocess.run(["gpio", "mode", str(self.LED_PIN_red), "out"])
        subprocess.run(["gpio", "mode", str(self.BUTTON_PIN_red), "in"])
        
        subprocess.run(["gpio", "mode", str(self.LED_PIN_blue), "out"])
        subprocess.run(["gpio", "mode", str(self.BUTTON_PIN_blue), "in"])
        
           
    def init_hd_thread(self):
        hd_threads = [threading.Thread(target=self.hd_detection_loop), 
                      threading.Thread(target=self.hd_detection_loop_2)]
        for hd_thread in hd_threads:
            hd_thread.start()
    
    @property
    def button_status(self):
        return self.shared_hd_status
        
    def hd_detection_loop(self):
        keyboard_status = False
        while True:
            self.shared_hd_status = True if subprocess.run(["gpio", "read", str(self.BUTTON_PIN_red)], capture_output=True, text=True).stdout.strip() == '0' else False
            if self.shared_hd_status:
                # 打开LED（输出高电平）
                subprocess.run(["gpio", "write", str(self.LED_PIN_red), "1"])
            else:
                # 关闭LED（输出低电平）
                subprocess.run(["gpio", "write", str(self.LED_PIN_red), "0"])

            global t, last_status
            if not self.shared_hd_status and last_status:
                print(f"pres time: {datetime.datetime.now()}")
            last_status = self.shared_hd_status
            t+=1
    
    @property
    def button2_status(self):
        return self.shared_hd_status_2
    
    def hd_detection_loop_2(self):
        keyboard_status = False
        while True:
            self.shared_hd_status_2 = True if subprocess.run(["gpio", "read", str(self.BUTTON_PIN_blue)], capture_output=True, text=True).stdout.strip() == '0' else False
            if self.shared_hd_status_2:
                # 打开LED（输出高电平）
                subprocess.run(["gpio", "write", str(self.LED_PIN_blue), "1"])
            else:
                # 关闭LED（输出低电平）
                subprocess.run(["gpio", "write", str(self.LED_PIN_blue), "0"])
    
    def set_led1_on(self):
        subprocess.run(["gpio", "write", str(self.LED_PIN_red), "1"])
        
    def set_led1_off(self):
        subprocess.run(["gpio", "write", str(self.LED_PIN_red), "0"])
    
    def set_led2_on(self):
        subprocess.run(["gpio", "write", str(self.LED_PIN_blue), "1"])
        
    def set_led2_off(self):
        subprocess.run(["gpio", "write", str(self.LED_PIN_blue), "0"])