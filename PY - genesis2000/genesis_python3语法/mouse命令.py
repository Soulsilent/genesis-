#!python3

from tkinter import *
import tkinter.messagebox as messagebox

def gu_mess(info_1,info_2='泉哥提示'):
    root = Tk()
    root.withdraw() #隐藏父窗口
    root.wm_attributes('-topmost',1) #窗口置顶    
    messagebox.showinfo(info_2,info_1)





import Genesis
g = Genesis.Genesis()
##g.PAUSE('SS')
aa = g.MOUSE('r get_area')  
bb = g.MOUSEANS #这里接收的是四个坐标

aa = g.MOUSE('p get_area') 
bb = g.MOUSEANS #这里接收的是2个坐标


g.PAUSE(aa[0])

gu_mess(bb)
