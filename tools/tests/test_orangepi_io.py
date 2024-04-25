import subprocess
from datetime import datetime
import time

# 定义引脚编号
BUTTON_PIN = 8  # 假设按键连接到GPIO 8号引脚
LED_PIN = 5     # 假设LED连接到GPIO 5号引脚

BUTTON_PIN = 6  # 假设按键连接到GPIO 8号引脚
LED_PIN = 2     # 假设LED连接到GPIO 5号引脚

# 初始化GPIO模式
subprocess.run(["gpio", "mode", str(LED_PIN), "out"])
subprocess.run(["gpio", "mode", str(BUTTON_PIN), "in"])

try:
    while True:
        print("start: ", datetime.now())
        # 读取按键状态
        button_state = subprocess.run(["gpio", "read", str(BUTTON_PIN)], capture_output=True, text=True)
        button_state = button_state.stdout.strip()

        # 如果按键被按下（假设按下为低电平）
        if button_state == '0':
            # 打开LED（输出高电平）
            subprocess.run(["gpio", "write", str(LED_PIN), "1"])
        else:
            # 关闭LED（输出低电平）
            subprocess.run(["gpio", "write", str(LED_PIN), "0"])

        print("end: ", datetime.now())
        # 稍作延时
        # time.sleep(0.1)

except KeyboardInterrupt:
    print("Program terminated by user")