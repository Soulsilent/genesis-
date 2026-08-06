#!python3
from tkinter import *
import tkinter.messagebox as messagebox
import tkinter.font as tkFont
import os,dbm
import Genesis
g = Genesis.Genesis()

def set_mess(info='?'):
    root = Tk()
    root.withdraw() #隐藏父窗口
    root.wm_attributes('-topmost',1) #窗口置顶    
    messagebox.showinfo("泉哥提示",info)

dbm_path = os.getenv("GENESIS_DIR")+'/share/tmp'
if not os.path.exists(dbm_path): #判断文件夹是否存在
    os.makedirs(dbm_path)   
dbm_path = dbm_path+'/py_shave_pad' #数据库文件

class my_dbm(object):
  
    def __init__(self):
        self.my_shave = 127
              
    def set_compare(self,value1):
        self.db = dbm.open(dbm_path,'c')
        self.db['shavePad']  = '{}'.format(value1) 
        self.db.close()
        
    def get_compare(self):
        self.db           = dbm.open(dbm_path,'c')
        if self.db:               
            self.my_shave = self.db['shavePad'].decode('utf-8')            
        self.db.close()           
        return self.my_shave

        
class Application(Frame):
    
    def __init__(self,master=None):
        Frame.__init__(self,master) #Frame要大写
        #self.pack() #这两个布局模式不应该同时出现
        self.grid()
        self.createwidgets()

    #标题控件封装
    def cre_label(self,text,row,col,*,padx=10,pady=10): 
        self.ft = tkFont.Font(family = 'Fixdsys',size = 14,weight = tkFont.BOLD)        
        self.w = Label(self,text=text,font=self.ft)
        self.w.grid(row=row,column=col,padx=padx,pady=pady)  #注意,这两行要分开,不然无法返回地址
        return self.w  #返回建立函数的地址

    
    #文本框封装
    def cre_entry(self,row,col,text='',*,padx=10,pady=10):
        self.ft = tkFont.Font(family = 'Fixdsys',size = 14,weight = tkFont.BOLD) 
        self.tmp = StringVar()
        self.tmp.set(text)
        self.w = Entry(self,textvariable=self.tmp,font=self.ft)
        self.w.grid(row=row,column=col,padx=padx,pady=pady)
        return self.w

    #下拉选项框封装
    def cre_optionmenu(self,row,col,value,*text,padx=10,pady=10,sticky=EW):
        self.ft = tkFont.Font(family = 'Fixdsys',size = 14,weight = tkFont.BOLD)
        self.tmp = StringVar()
        self.tmp.set(value)
        self.w = OptionMenu(self,self.tmp,*text)  #如果text不带*号时,数据会合并成字符串
        self.w.config(font=self.ft) #此处设置背景,前景和字体
        self.w.grid(row=row,column=col,padx=padx,pady=pady,sticky=sticky)        
        ##return self.w
        ##注意,下拉列表optionmenu获取数据是通过当前值变量获取的,所以要返回self.tmp
        return self.tmp  

    def cre_button(self,row,col,command,text='default',\
                   padx=10,pady=10,sticky=EW,columnspan=1):
        self.ft = tkFont.Font(family = 'Fixdsys',size = 14,weight = tkFont.BOLD)         
        self.w = Button(self,text=text,command=command,font=self.ft)
        self.w.grid(row=row,column=col,padx=padx,pady=pady,sticky=sticky,columnspan=columnspan)
        return self.w

    def createwidgets(self):

        self.cre_label(r'ShavePad间距(my):',0,0)
        my_data = my_dbm().get_compare() #获取DBM数据
        self.entry_1 = self.cre_entry(0,1,my_data)
        self.b1 = self.cre_button(5,0,self.bt1,'保存参数',columnspan=2)
        self.b2 = self.cre_button(6,0,self.quit,'退出',columnspan=2)        

    def bt1(self):
        set_mess('参数已保存!\n'+self.entry_1.get()+'my')

        ##保存DBM数据 
        my_dbm().set_compare(self.entry_1.get())




def shave_Pad(index1,index2,layer,space,mode1,mode2):
    
    
    modes = ['shave','none','move_triplet']   
    g.COM("space_edit,fidx1={},fidx2={},layer1={},mode1={},mode2={},common_shave=no,space={}"\
          .format(index1,index2,layer,modes[mode1],modes[mode2],space))

if g.JOB==None or g.STEP==None:
    set_mess('请在JOB/STEP内运行脚本')
    exit(0)    
else:
    

    g.COM("open_entity,job={JOB},type=step,name={STEP},iconic=no"\
          .format(JOB=g.JOB,STEP=g.STEP))
    g.AUX(g.COMANS)


    myNum = int(g.COM("get_select_count"))
    if myNum!=2:        
        app = Application()
        app.master.title('ShavePad参数设置')
        app.master.wm_attributes('-topmost',1) #窗口置顶   
        app.master.geometry('+800+300') #设置窗口位置
        app.mainloop()
        exit(0)

    else:
        myLayer = g.COM("get_work_layer")
        file_pad = g.INFO(r'-t layer -e {JOB}/{STEP}/{layer} -m script -d FEATURES -o feat_index+select'\
                    .format(JOB=g.JOB,STEP=g.STEP,layer=myLayer),mode=2)
        import re
        xa = re.match(r'#(\d*)\s?#(\D).*?(?:\.(\D*))?$',file_pad[1])
        xb = re.match(r'#(\d*)\s?#(\D).*?(?:\.(\D*))?$',file_pad[2])
        
        if xa.group(2)==xb.group(2)=='L':
            exit(0)
        my_shave = my_dbm().get_compare() #获取DBM数据
        if g.COM('get_units')=='inch':
            my_shave = float(my_shave)/25.4
            
        #set_mess(my_shave)
        # 0 削,1 无动作 ,2 绕线 

        if xa.group(2)=='L':
            if xb.group(3):
                shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,2,1)
            else:
                shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,1,0)
        else:
            if xb.group(2)=='P':
                if xa.group(3):
                    if xb.group(3):
                        shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,0,0)
                    else:
                        shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,1,0)
                else:
                    if xb.group(3):
                        shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,0,1)
                    else:
                        shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,0,0)                    
            else:
                if xa.group(3):
                    shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,1,2)
                else:
                    shave_Pad(xa.group(1),xb.group(1),myLayer,my_shave,0,1)

            




