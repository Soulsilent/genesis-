#!python3
import Genesis
g = Genesis.Genesis()



from tkinter import *
import tkinter.messagebox as messagebox

def gu_mess(info_1,info_2='泉哥提示'):
    root = Tk()
    root.withdraw() #隐藏父窗口
    root.wm_attributes('-topmost',1) #窗口置顶    
    messagebox.showinfo(info_2,info_1)
    
    








def get_step(v_job):
 
    #传入料号,返回单元列表
    #获取矩阵数据
    g.INFO('-t matrix -e {}/matrix -m script'.format(v_job))
    vsteps = g.DO_INFO['gCOLstep_name']  #单元名称(含空单元)
    #删除空单元
    while '' in vsteps:
        vsteps.remove('')
    return vsteps        

#gu_mess(get_step(g.JOB))          
        
def get_layer(v_job):

    pass


   
   
   
   
  
