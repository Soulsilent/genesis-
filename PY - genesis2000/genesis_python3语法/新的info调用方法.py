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


#g.INFO('-t step -e {JOB}/{STEP} -m script'.format(JOB=g.JOB,STEP=g.STEP))
##g.INFO("-t step -e " + g.JOB + "/" + g.STEP,unit="inch") #默认MM格式
##g.INFO("-t step -e " + g.JOB + "/" + g.STEP)

g.INFO('-t matrix -e {}/matrix -m script'.format(g.JOB))

#不管是下面哪种方法,调用的时候,中途都不能再次info,否则数据丢失,如果需要反复使用,请找好变量容器装好这些数据!

#第一种调用方法
#aa=g.DO_INFO["gLAYERS_LIST"] #返回一个list列表
##g.PAUSE(aa[2]) #PAUSE不能显示list,只能显示list的某个元素
#gu_mess(aa) #显示所有元素



#第二种调用方法
#gu_mess(g.gLAYERS_LIST) #显示所有元素
# gu_mess(g.gROWcontext)













# g.PAUSE(g.get_units)  #获取单位 str
# g.PAUSE(g.get_affect_layer)   #获取影响层 ,数组[n,m]
# g.PAUSE(g.get_disp_layers)  #显示层,数组[n,m]
# g.PAUSE(g.get_message_bar)  #底部信息,数组[n,m]
# g.PAUSE(g.get_origin)  #原点[x,y]

# g.PAUSE(g.get_select_count)  #选中数量
# g.PAUSE(g.get_work_layer)
# g.PAUSE(g.get_user_group)
# g.PAUSE(g.get_user_name)



