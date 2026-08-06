#!python3
import sys
print('''
    sys.argv是argument variable参数的简写形式,
    在命令行调用的时候,由系统传递给程序
    使用这个函数,可以获取Genesis运行时的临时文件的位置
    通过读取文件来获取lnPARAM 和lnVAl这两个=号左右的值!

    注意,返回的是[]列表,要使用[0]消除方框后open
    f1 = open(sys.argv[1:2][0])
    for x in f1:       
        set_mess(x)    
    
''')

print('打印所有参数',sys.argv[:])
for x in sys.argv:
    print(x)

