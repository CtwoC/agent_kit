import sys
import os
 
# 将client目录添加到Python路径中，这样可以直接导入client模块
current_dir = os.path.dirname(os.path.abspath(__file__))
client_dir = os.path.dirname(current_dir)
if client_dir not in sys.path:
    sys.path.insert(0, client_dir) 