from enum import Enum
import platform

class Color(Enum):
    RESET = '\033[0m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'

def printc(msg, color):
    if platform.system() == 'Linux':
        print(color.value+msg+Color.RESET.value)
    else:
        print(msg)