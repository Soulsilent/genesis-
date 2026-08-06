#!python3
import os,sys
gateway = r'C:\genesis\e100\misc\gateway.exe'

print(gateway)

'''
os.popen('{} COM clipb_open_job,job=1,update_clipboard=view_job'.format(gateway))

os.system('{} COM open_job,job=1'.format(gateway))





import commands
status, output = commands.getstatusoutput("ls")
commands模块是python的内置模块 共有三个函数，使用help（commands）可以查到。
status代表的shell命令的返回状态，如果成功的话是0；output是shell的返回的结果


#python3中取消了commands,使用subprocess替换

import subprocess

subprocess.run()  #单纯执行

subprocess.call() #执行命令，返回命令的结果和执行状态，status  0或者非0 

subprocess.check_call() 执行命令，返回结果和状态，正常为0 ，执行错误则[[[抛出异常 ]]]

subprocess.getstatusoutput() 接受字符串形式的命令，
    返回 一个元组形式的结果，第一个元素是命令执行状态，第二个为执行结果


subprocess.getoutput() 接受字符串形式的命令，放回执行结果 ,要结果用这个




subprocess.check_output() 执行命令，返回执行的结果，而不是打印

相当于可以用变量接收结果,返回的是b' ' 字节类型,不常用

'''
import subprocess

res = subprocess.getoutput('ls') 
#print(res) #打印结果


res = subprocess.getstatusoutput('ls') 
#print(res) #打印结果

aa = r'C:/genesis/e100/misc/gateway.exe %8880@DESKTOP-ODH4NFM.DESKTOP-ODH4NFM "COM script_run,name=C:/genesis/sys/scripts/py/pause.py,env1=job=ns48162a,env2=step=edit,env3=MODE=up"'

#aa = r'C:/genesis/e100/misc/gateway.exe %8880@DESKTOP-ODH4NFM.DESKTOP-ODH4NFM "COM save_job,job=ns48162a,override=yes"' #成功

#aa = r'C:/genesis/e100/misc/gateway.exe %8880@DESKTOP-ODH4NFM.DESKTOP-ODH4NFM "PAUSE A"' #error 不支持PAUSE,可能...


#res = subprocess.getstatusoutput(aa) 

print('---')

res = subprocess.call(aa) 



print(res) #打印结果


