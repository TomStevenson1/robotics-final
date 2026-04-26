import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/liuutin9/Desktop/robotics-final/youting_src/yt_ws/install/final_package'
