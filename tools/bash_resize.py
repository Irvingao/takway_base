import os
import cv2

def resize_video(input_video_path, output_video_path, new_size=(240, 240), fps=30.0):
    """
    Resize a video to a new size.

    :param input_video_path: Path to the input video file.
    :param output_video_path: Path where the resized video will be saved.
    :param new_size: New size of the video as a tuple (width, height).
    :param fps: Frames per second of the output video.
    """
    # 打开视频文件
    cap = cv2.VideoCapture(input_video_path)

    # 获取视频编码格式
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # 创建视频写入对象
    out = cv2.VideoWriter(output_video_path, fourcc, fps, new_size)

    # 读取视频帧并调整尺寸
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 调整帧尺寸
        resized_frame = cv2.resize(frame, new_size)

        # 写入调整后的帧
        out.write(resized_frame)

    # 释放资源
    cap.release()
    out.release()

# 示例用法
# resize_video('path/to/your/900x900_video.mp4', 'path/to/your/240x240_video.mp4')

def process_directory(input_root, output_root):
    """
    Process all MP4 files in the directory structure under input_root.
    Each file will be resized and saved to a mirrored directory structure under output_root.
    """
    # 遍历输入根目录
    for root, dirs, files in os.walk(input_root):
        for file in files:
            if file.endswith('.mp4'):
                # 构建完整的文件路径
                input_path = os.path.join(root, file)

                # 创建输出目录结构
                relative_path = os.path.relpath(root, input_root)
                output_dir = os.path.join(output_root, relative_path)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                # 设置输出文件路径
                output_path = os.path.join(output_dir, file)

                # 调整视频尺寸
                resize_video(input_path, output_path)

# 示例用法
input_root = 'Emoji'
output_root = 'ResizedEmoji'
process_directory(input_root, output_root)
