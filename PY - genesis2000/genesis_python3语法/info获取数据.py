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

'''
g.INFO('xxx',unit="inch",mode=2)

info后面的两个参数默认是MM和1

分别控制数据单位的inch和是否要整理数据(用于获取D码FEATURES)
可以省略,但是不缺省的时候,不能写'inch',要写unit='inch',因为是字典格式,也可以只缺省一个参数




'''



##原始格式csh数据
##-t step -e s2p14935a0/edit -m script

##转换格式,默认MM格式,
##g.INFO('-t step -e {JOB}/{STEP} -m script'.format(JOB=g.JOB,STEP=g.STEP))
##g.INFO("-t step -e " + g.JOB + "/" + g.STEP,unit="inch") #默认MM格式
##g.INFO("-t step -e " + g.JOB + "/" + g.STEP)

##aa=g.DO_INFO["gLAYERS_LIST"] #返回一个list列表
##g.PAUSE(aa[2]) #PAUSE不能显示list,只能显示list的某个元素
##gu_mess(aa) #显示所有元素
##gu_mess(len(aa)) #显示元素数量





##-t layer -e s2p14935a0/edit/to -m script
##g.INFO('-t layer -e {JOB}/{STEP}/{layer} -m script'.format(JOB=g.JOB,STEP=g.STEP,layer='ts'),unit="inch")
##
##aa=g.DO_INFO["gSYMS_HISTsymbol"] #返回一个list列表
##aa=g.DO_INFO['gFEAT_HISTtotal'] #返回一个元素

##g.PAUSE(aa) #PAUSE不能显示list,只能显示list的某个元素






##-t layer -e s2p14935a0/edit/gko -m script -d FEATURES
aa = g.INFO('-t layer -e {JOB}/{STEP}/{layer} -m script -d FEATURES'.format(JOB=g.JOB,STEP=g.STEP,layer='gko'),mode=2,unit="inch")



gu_mess(aa[:4]) #显示所有元素
gu_mess(len(aa)) #显示元素数量
