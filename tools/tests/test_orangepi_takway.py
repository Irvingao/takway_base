from takway.board.orangepi import OrangePi

from datetime import datetime

if __name__ == '__main__':
    board = OrangePi()
    
    while True:
        print(f"{datetime.now()}: {board.is_hardware_pressed()}")