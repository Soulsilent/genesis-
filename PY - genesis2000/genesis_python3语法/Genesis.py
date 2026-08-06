#!/usr/bin/env python
# coding:utf-8

__author__ = "huang min cai"
__date__ = "2019-12-02"
__version__ = "Revision: 1.0.0"

import os
import re
import sys
import socket

class Genesis():

    def __init__(self, isSocket=False, host='localhost', port=56753):
        self._isSocket = isSocket  # 控制是否调试的开关
        self._host = host  #远程服务器,默认是本机
        self._port = port  #端口,默认56753
        self.DIR_PREFIX = '@%#%@'
        self.GENESIS_DIR = os.getenv('GENESIS_DIR')  # C:/genesis
        self.GENESIS_EDIR = os.getenv('GENESIS_EDIR')  # C:/genesis/e100
        self.GENESIS_TMP = os.getenv('GENESIS_TMP')  # C:/tmp
        self.ALL_VALUE = ''  # 获取到的所有返回值数据
        self.__blank()
        self.DO_INFO = {}  # 一个字典容器,存储info整理出来的信息
        if self._isSocket:
            # 默认不调试,内挂,直接读取环境变量中的料号和单元数据
            print('进入调试模式')
            if not sys.stdin.isatty():
                #isatty,检测服务端是否有启动,如果没有启动,那么就要让Genesis运行server.py
                #todo
                print('服务端未开启')
            if self._createSocket(): #创建客户端连接
                self._recvENV()  #传入指令,要求服务端返回它那边的环境变量
            else:
                #如果返回False,说明连接服务端失败,取消socket开关,转为普通模式
                self._isSocket = False

        #要判断是否调试之后才能获取JOB/STEP
        self.JOB = os.getenv('JOB')
        self.STEP = os.getenv('STEP')


    def _createSocket(self):
        self.gSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 声明socket类型，同时生成链接对象
        try:
            self.gSocket.connect((self._host, self._port))  # 建立一个链接，连接到服务器/本地的指定端口
        except:
            return False  #判断连接是否成功
        return True

    def __del__(self):
        if self._isSocket:
            #socket模式,注销类对象时,同时关闭服务端的监听信号!
            self.gSocket.send('CLOSEDOWN'.encode('utf-8'))  #发送关闭指令

    def _recvENV(self):
        #接收服务端传递过来的环境变量
        self.gSocket.send('GETENVIRONMENT'.encode('utf-8'))  #向服务端发送获取环境变量的请求
        while True:
            #进入无限循环,等待回传的数据 #接收返回数据,并指定接收大小为1024字节
            gKey = self.gSocket.recv(1024)
            if gKey.decode() == 'END':
                # 传来END,代表数据传输完毕!,退出循环
                print('接收环境变量完毕!')
                break
            print('KEY数据:{}'.format(gKey.decode()))

            gValue = self.gSocket.recv(1024)

            if gValue.decode() in ['None','']:
                os.environ[gKey.decode()] = ''
            else:
                os.environ[gKey.decode()] = gValue.decode()
            print('VAL数据:{}'.format(gValue.decode()))

            self.gSocket.send('NEXT'.encode('utf-8'))  #发送下一个数据过来



    def __getattr__(self, item):
        # 返回一个属性对应的值,  有这个魔法方法,可以直接g.gROWname 这样直接调用INFO结果
        if item in self.DO_INFO:
            # 返回info参数
            return self.DO_INFO[item]
        else:
            self.PAUSE('{} the name by not Info or is deled'.format(item))
            raise Exception('{}这个参数没有info过,或者已经info但是已被删除!'.format(item))

    def __blank(self):
        # 五种返回值,全部重置为空
        self.STATUS = ""
        self.COMANS = ""
        self.MOUSEANS = ""
        self.PAUSANS = ""
        self.READANS = ""

    def __write(self, command):
        self.__blank()  # 清空返回状态
        data_out = self.DIR_PREFIX + command + "\n"
        if self._isSocket:
            #调试模式,数据传给网络端口
            self.gSocket.send(data_out.encode('utf-8'))
            self.gSocket.recv(1024)  #等待回传ok信号
        else:
            #普通模式,数据直接输出到控制台
            sys.stdout.write(data_out)  # 将指令写入控制台
            sys.stdout.flush()  # 刷新缓冲区

    def __read(self):
        try:
            if self._isSocket:
                #调试模式,读取网络传回的数据
                self.gSocket.send('GETREPLY'.encode('utf-8'))  #发送指令,要求服务端读取那边控制台的返回值,并回传过来
                value = self.gSocket.recv(124).decode()
                #如果是Bool,None或者null,需要重新整理
                if value == 'True':
                    value = True
                elif value == 'False':
                    value = False
                elif value == 'None':
                    value = None
                    sys.exit(0)  #没有返回值,应该是PAUSE退出了!
                elif value == 'null':
                    value = ''
            else:
                #普通模式,直接读取传入参数
                value = input()
        except:
            # 当PAUSE直接退出时,会没有返回值,如果有这句话,就需要自己判断后再退出!
            value = 'exit'
            sys.exit(0)
        return value

    def COM(self, command):
        self.__blank()
        self.__write("COM {}".format(command))
        self.STATUS = self.__read()
        self.READANS = self.__read()
        self.COMANS = self.READANS
        self.ALL_VALUE = 'STATUS:{}\nCOMANS:{}\nREADANS:{}'.format(self.STATUS, self.COMANS, self.READANS)
        return self.COMANS

    def AUX(self, group):
        self.__blank()
        self.__write("AUX set_group,group=" + group)
        self.STATUS = self.__read()
        self.READANS = self.__read()
        self.COMANS = self.READANS
        self.ALL_VALUE = 'STATUS:{}\nCOMANS:{}\nREADANS:{}'.format(self.STATUS, self.COMANS, self.READANS)
        return self.COMANS

    def VON(self):
        self.__blank()
        self.__write("VON")

    def VOF(self):
        self.__blank()
        self.__write("VOF")

    def SU_ON(self):
        self.__blank()
        self.__write("SU_ON")

    def SU_OFF(self):
        self.__blank()
        self.__write("SU_OFF")

    def MOUSE(self, command):
        self.__blank()
        self.__write("MOUSE {}".format(command))
        self.STATUS = self.__read()
        self.READANS = self.__read()
        self.MOUSEANS = self.__read().split()
        self.ALL_VALUE = ' STATUS:{}\n READANS:{}\n MOUSEANS:{}'.format(self.STATUS, self.READANS, self.MOUSEANS)
        return self.MOUSEANS

    def PAUSE(self, command):
        self.__blank()
        self.__write("PAUSE {}".format(command))
        self.STATUS = self.__read()
        self.READANS = self.__read()
        self.PAUSANS = self.__read()
        self.ALL_VALUE = ' STATUS:{}\n READANS:{}\n PAUSANS:{}'.format(self.STATUS, self.READANS, self.PAUSANS)
        return self.PAUSANS

    def INFO(self, command, *, unit="mm", mode=1):
        # 先准备一个空容器
        self.DO_INFO = {}
        flie_tmp = os.getenv("GENESIS_TMP") + "/genesis_python.tmp"
        ##units = "units=mm"
        if unit.lower() != "units=mm" and unit.lower() != 'mm':
            units = "units=inch"
        else:
            units = "units=mm"
        args = "info,out_file=" + flie_tmp + "," + units + ",args=" + command
        self.COM(args)

        with open(flie_tmp, 'r', errors = 'ignore') as f1:
            flie = f1.readlines()  # 增加errors='ignore',编码错误忽略

        os.unlink(flie_tmp)

        if mode != 1:  # 直接返回打开的数据文件内容,不调整
            return flie

        for arge in flie:
            regex = re.match("^set\s+(\S+)\s+=\s+(.*?)\n", arge)  # 匹配set gtoolxxx  =  all   #

            if regex != None:
                value1 = regex.group(1)
                value2 = regex.group(2)

                # value3 = re.findall("('\S*')",value2)  #如果匹配括号,3非空,此处错误,无法分辨本身存在的空格
                value3 = re.findall("('.*?')", value2)  # 如果匹配括号,3非空

                # self.PAUSE(type(value2))
                # value3 = value2.strip('()').split()  #删除()后,打散成列表
                # self.PAUSE(value3)

                if value3 != []:
                    value4 = [n.replace("'", "") for n in value3]
                    # value4 = [n[1:-1] for n in value3]  #去除头尾的''号
                    # value4 = map(lambda x:x[1:-1],value3)

                    if re.match("\(", value2):  # 如果匹配有(号在2的开头
                        self.DO_INFO[value1] = value4  # 返回去除' '号后的值列表

                    else:
                        self.DO_INFO[value1] = value4[0]  #
                else:
                    self.DO_INFO[value1] = value2  # 只有一个值

    # 常用的九种get方法
    @property
    def get_units(self):
        # 通过g.get_units 获取返回的单位,返回值为str字符串
        return self.COM('get_units')

    @property
    def get_affect_layer(self):
        # 通过g.get_affect_layer 获取返回的影响层,返回结果为数组[n,m]
        return self.COM("get_affect_layer").split()

    @property
    def get_disp_layers(self):
        # 获取显示层,返回数组[n,m]
        return self.COM("get_disp_layers").split()

    @property
    def get_message_bar(self):
        # 返回编辑器底部信息,返回结果为数组[n,m]
        return self.COM("get_message_bar").split(',')

    @property
    def get_origin(self):
        # 获取图形原点 [x,y]
        return self.COM("get_origin").split()

    @property
    def get_select_count(self):
        # 返回选择数量,返回值为整数类型
        return int(self.COM("get_select_count"))

    @property
    def get_work_layer(self):
        # 返回当前工作层,返回值为字符串
        return self.COM("get_work_layer")

    @property
    def get_user_group(self):
        # 返回用户所属组的名称 ,cam或者1
        return self.COM("get_user_group")

    @property
    def get_user_name(self):
        # 返回当前登录到系统中的用户名 , 1
        return self.COM("get_user_name")


if __name__ == '__main__':
    pass
