import time
import sys

"""
为了部署能正常运行，看到错误日志，特加的循环执行脚本
"""

while True:
    print(f'{time.localtime()}')
    sys.stdout.flush()
    time.sleep(300)
