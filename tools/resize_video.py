import cv2

# 输入和输出文件路径
input_video_path = r'Emoji\兴奋\兴奋_1进入姿势.mp4'
output_video_path = r'Emoji\兴奋\240x240_兴奋_1进入姿势.mp4'

# 打开视频文件
cap = cv2.VideoCapture(input_video_path)

# 获取视频编码格式
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

# 创建视频写入对象
out = cv2.VideoWriter(output_video_path, fourcc, 30.0, (240, 240))

# 读取视频帧并调整尺寸
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 调整帧尺寸
    resized_frame = cv2.resize(frame, (240, 240))

    # 写入调整后的帧
    out.write(resized_frame)

# 释放资源
cap.release()
out.release()
