#!python3
import sys,re
from tkinter import *
import tkinter.messagebox as messagebox
def set_mess(info='?'):
    root = Tk()
    root.withdraw() #隐藏父窗口
    root.wm_attributes('-topmost',1) #窗口置顶    
    messagebox.showinfo("泉哥提示",info)
    

apth = r'F:\1\ORIG\222.1'

f2 = open(apth)
moin = 0
for f_date in f2:
    
    if (r'%MOIN*%' in f_date): #判断gerber文件的单位
        #print(f_date)
        moin = 1  #英制
        next   
    if (r'%MOMM*%' in f_date):
        #print(f_date)
        moin = 2  #公制
        next
    if(moin != 0): #只有找到gerber单位后才执行操作
        if ('%ADD' in f_date):  #只打印D码表
            aa = re.match(r'.*?\,(.*?)(?:\*%)',f_date).group(1)
            #获取D码大小
            if not ('X' in aa):
                aa = float(aa)    
                #print(aa)
                if (moin == 2): #公制单位MM,转换为inch
                    aa = aa/25.4
                    #print(aa)
                if (aa < 0.003):
                    print(aa,'error')
                    set_mess(apth)
                    break            # 跳出当前循环
                

                


