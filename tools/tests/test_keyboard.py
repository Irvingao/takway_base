import keyboard

def exit_program(event):
    if event.name == "space":
        print("程序退出...")
        exit()

# print("按住空格键退出程序")
# keyboard.on_press(exit_program)
# keyboard.wait()
while True:
    print(keyboard.is_pressed("space"))