#!python3

from tkinter import Tk
import tkinter.messagebox as messagebox
import time



def set_mess(info='?'):
    root = Tk()
    root.withdraw() #隐藏父窗口
    root.wm_attributes('-topmost',1) #窗口置顶    
    messagebox.showinfo("提示",info)
    





def get_time(f):
    def inner(*arg,**kwarg):
        s_time = time.time()
        res = f(*arg,**kwarg)
        e_time = time.time()
        set_mess('耗时：{}秒'.format(e_time - s_time))
        return res
    return inner






    
    
if __name__ == '__main__':

    @get_time
    def test():
        time.sleep(2)  # 模拟运行2s

    test()
    # set_mess('fff')

    print('ok')
