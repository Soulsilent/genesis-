#!python3
import os
import re
import subprocess
import win32gui
from ctypes import windll, c_char_p
from GenesisAddress import get_address
from pathlib import Path
from set_mess import set_mess


class GenesisGateway:

    def __init__(self, job_ver='JOB_10.00', step_ver='STEP_10.00'):
        # 默认10.0版本
        self.job_ver = job_ver
        self.step_ver = step_ver
        self.job_address, self.step_address = get_address()  # 获取内存基址

    def set_job_step_ver(self,job_ver, step_ver):
        # 更新地址版本
        self.job_ver = job_ver
        self.step_ver = step_ver

    def get_genesis_PID(self):
        # 通过窗口类名,找到窗口句柄,Genesis的窗口类名是固定的,使用spy++找到的'Xmanager:XFrame'
        hWnd = win32gui.FindWindow('Xmanager:XFrame', None)
        # print(hWnd)
        # 通过句柄,查找标题或者窗口内容
        text = win32gui.GetWindowText(hWnd)
        if mth := re.match(r'.*?pid:(\d+)?', text):
            return mth.groups()[0]

    def get_JobsStepName(self, myPid, getval='job'):
        # JOB_10.00 => 0313C384
        # STEP_10.00 => 0313C2BD

        # 要么获取job,要么获取step
        address = self.job_address[self.job_ver] if getval == 'job' else self.step_address[self.step_ver]

        kernel32 = windll.LoadLibrary("kernel32.dll")  # 加载kernel32.dll
        ReadProcessMemory = kernel32.ReadProcessMemory  # 获得ReadProcessMemory函数地址
        # 权限要足够,0x1F0FFF
        OpenProcess = kernel32.OpenProcess(0x1F0FFF, False, int(myPid))
        buffer = c_char_p(b"_" * 256)  # 缓冲区地址
        # bufferSize = len(buffer.value)*10  # 缓冲区大小,十倍缓冲,防止高版本出错
        bufferSize = 256

        if ReadProcessMemory(OpenProcess, int(address, 16), buffer, bufferSize, None):
            # print(bytes.decode(buffer.value))
            return bytes.decode(buffer.value)
        else:
            # print('内存读取失败!')
            return None

    def get_host(self):  # 获取计算机名称
        if os.name == 'nt':  # windows系统
            return os.getenv('computername')
        elif os.name == 'posix':  # linux
            host = os.popen('echo $HOSTNAME')
            try:
                return host.read()
            finally:
                host.close()
        else:
            return 'Unkwon hostname'

    def script_run(self, myScript='', mode='script', runmode='None'):
        host = self.get_host()  # 获取主机名称
        gateway = f"{os.getenv('GENESIS_DIR')}/e{os.getenv('GENESIS_VER')}/misc/gateway.exe"

        myPid = self.get_genesis_PID()  # PID的值,Genesis窗口最小化时,无法获取pid
        # print(myPid)
        if not myPid:
            set_mess(
                '无Genesis进程PID!!!\n1.请确保已打开Genesis软件!\n2.请确保edit窗口没有最小化!\n3.请确保edit窗口上没有打开测量,过滤器,物件添加等子窗口..\n')
            return
        perfectpid = f'%{myPid}@{host}.{host}'
        VJOB = self.get_JobsStepName(myPid, getval = 'job')
        # print(VJOB)
        VSTEP = self.get_JobsStepName(myPid, getval = 'step')
        # print(VSTEP)
        if mode == 'script':
            myScript = Path(myScript)
            if not myScript.is_absolute():
                # 如果是相对路径,转为绝对路径
                myScript = myScript.absolute()

            # 只能返回错误代码****,和执行结果0,-1,1,无法返回具体数据,比如get_units无法获取单位
            myCommand = f'"COM script_run,name={myScript},env1=job={VJOB},env2=step={VSTEP},env3=runmode={runmode}"'
            return subprocess.getstatusoutput(f'{gateway} {perfectpid} {myCommand}\n')
        elif mode == 'COM':
            return subprocess.getstatusoutput(f'{gateway} {perfectpid} "{myScript}"\n')


if __name__ == '__main__':
    # myPid = get_genesis_PID()
    # get_JobsStepName(myPid)
    aa = GenesisGateway()  # 可以传入参数,设置Genesis版本
    bb = aa.script_run('COM units,type=mm', mode = 'COM')
    print(bb)

    # cc = aa.script_run(myScript = r'aaa1.py', runmode = '你好!')
    # print(cc)

    print('ok')
