#!python3
import sys
from tkinter import *
import tkinter.messagebox as messagebox
def set_mess(info='?'):
    root = Tk()
    root.withdraw() #隐藏父窗口
    root.wm_attributes('-topmost',1) #窗口置顶    
    messagebox.showinfo("泉哥提示",info)
line = sys.stdin   
print('sss')
try:
    if line:
        set_mess(line)
except:
    set_mess('无数据')
