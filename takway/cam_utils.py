try:
    import cv2
except:
    warnings.warn("OpenCV is not installed, please check the module if you need.")

class Camera:
    def __init__(self, 
                 device='pc',
                 width=1280, 
                 height=720):
        pass