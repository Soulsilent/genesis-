# Visit https://www.lddgo.net/string/pyc-compile-decompile for more information
# Version : Python 3.8

import subprocess
import re
import os
import sys,time
import ctypes
import win32gui
import win32api
import win32con


class genesis_gateway:
    __GATEWAY = os.getenv('GENESIS_EDIR') + '/misc/gateway.exe'
    __comans_file_tmp = os.getenv('GENESIS_TMP') + '/g_comans'
    __com_file_tmp = os.getenv('GENESIS_TMP') + '/g_com'
    __com_status = -1
    COMANS = []
    doinfo = {}

    def __init__(self):
        key = '   BINDING {\n        KEY=<Shift>F12\n        SCRIPT=C:/tmp/g_com\n   }\n'
        new = '第一次使用'
        bindings_file = os.getenv('GENESIS_DIR') + '\\sys\\bindings'
        if os.path.exists(bindings_file) == True:
            flie = open(bindings_file, 'r').readlines()
            i = 0
            for f in flie:
                if f.find('KEY=<Shift>F12') >= 0 and flie[i + 1].find('SCRIPT=C:/tmp/g_com') >= 0:
                    new = '旧'
                else:
                    i = i + 1
            # 修正：移除了 **('mode',) 错误语法
            if new == '第一次使用':
                file_handle = open(bindings_file, 'w')
                for f in flie:
                    file_handle.writelines(f)
                file_handle.writelines(key)
                file_handle.close()

    def get_genesis_edit_hwnd(self):
        hWnd = 0
        hWnd_list = []
        win32gui.EnumWindows((lambda hWnd, param: param.append(hWnd)), hWnd_list)
        for _hwnd in hWnd_list:
            title = win32gui.GetWindowText(_hwnd)
            if str(title).find('Graphic Editor') >= 0:
                hWnd = _hwnd
        return hWnd

    def __set_gateway_exe(self, gateway_exe):
        __GATEWAY = gateway_exe

    def __sendCommand(self):
        hwnd = self.get_genesis_edit_hwnd()
        if self.get_genesis_edit_hwnd() == 0:
            ctypes.windll.user32.MessageBoxW(0, '打开 genesis 编辑窗口才能运行脚本', '提示', 0)
            return None
        # 修正：None.PostMessage 改为 win32api.PostMessage
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_LSHIFT,
                             self.__MakeKeyLparam(win32con.VK_LSHIFT, win32con.WM_KEYDOWN))
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_F12,
                             self.__MakeKeyLparam(win32con.VK_F12, win32con.WM_KEYDOWN))
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_F12,
                             self.__MakeKeyLparam(win32con.VK_F12, win32con.WM_KEYUP))
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_LSHIFT,
                             self.__MakeKeyLparam(win32con.VK_LSHIFT, win32con.WM_KEYUP))
        self.__com_status = 0

    def __MakeKeyLparam(self, VirtualKey, flag):
        if flag == win32con.WM_KEYDOWN:
            Firstbyte = '00'
        else:
            Firstbyte = 'C0'
        Scancode = win32api.MapVirtualKey(VirtualKey, 0)
        Secondbyte = str('00' + hex(Scancode))
        Secondbyte = Secondbyte[len(Secondbyte) - 2:]
        s = Firstbyte + Secondbyte + '0001'
        return int(s, 16)

    def __gateway_com(self, com_str):
        self.__com_status = -1
        hostname = os.getenv('computername')
        cmd_pid = 'tasklist | grep get.exe'
        # 修正：移除了 **('shell', 'stdout') 错误语法，改为关键字参数
        get_info = subprocess.Popen(cmd_pid, shell=True, stdout=subprocess.PIPE)
        for line in get_info.stdout.readlines():
            pid_info = line.decode('utf-8').strip()
            pid_list = pid_info.split()
        pid = pid_list[1]
        pid_str = '%' + pid + '@' + hostname + '.' + hostname
        cmd = self.__GATEWAY + ' ' + pid_str + ' ' + '"COM %s' % com_str + '"'
        res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        (out, err) = res.communicate()
        for res in out.splitlines():
            # 修正：移除了 **('encoding',) 错误语法
            res_flag = str(res, 'utf8')
            self.__com_status = int(res_flag)
            print(res_flag)

    def genesis_script_run(self, script_path):
        script_path = f'''"{script_path}"'''
        self.__gateway_com('script_run,name=' + script_path + ',dirmode=global,params=')

    def COM(self, command):
        if os.path.exists(self.__comans_file_tmp) == True:
            os.unlink(self.__comans_file_tmp)
        # 修正：移除了 **('mode',) 错误语法
        file_handle = open(self.__com_file_tmp, 'w')
        l1 = 'COM %s\n' % command
        l2 = 'echo $COMANS > ' + self.__comans_file_tmp
        file_handle.writelines([
            l1,
            l2])
        file_handle.close()
        self.__sendCommand()
        if self.__com_status == 0:
            if os.path.exists(self.__comans_file_tmp):
                self.COMANS = open(self.__comans_file_tmp, 'r').readline().strip()
                if len(self.COMANS) == 0:
                    self.COMANS = -1

                os.unlink(self.__comans_file_tmp)
                return None

    def STEP(self):
        if os.path.exists(self.__comans_file_tmp) == True:
            os.unlink(self.__comans_file_tmp)
        # 修正：移除了 **('mode',) 错误语法
        file_handle = open(self.__com_file_tmp, 'w')
        l1 = 'echo $STEP > ' + self.__comans_file_tmp
        file_handle.writelines([
            l1])
        file_handle.close()
        self.__sendCommand()
        if self.__com_status == 0:
            if os.path.exists(self.__comans_file_tmp):
                self.COMANS = open(self.__comans_file_tmp, 'r').readline().strip()
                if len(self.COMANS) == 0:
                    self.COMANS = -1

                os.unlink(self.__comans_file_tmp)
                return self.COMANS

    def JOB(self):
        if os.path.exists(self.__comans_file_tmp) == True:
            os.unlink(self.__comans_file_tmp)
        file_handle = open(self.__com_file_tmp, 'w')
        l1 = 'echo $JOB > ' + self.__comans_file_tmp
        file_handle.writelines([
            l1])
        file_handle.close()
        self.__sendCommand()

        # 新增：等待 Genesis 执行命令
        time.sleep(0.2)

        if self.__com_status == 0:
            if os.path.exists(self.__comans_file_tmp):
                self.COMANS = open(self.__comans_file_tmp, 'r').readline().strip()
                if len(self.COMANS) == 0:
                    self.COMANS = -1

                if os.path.exists(self.__comans_file_tmp) == True:
                    os.unlink(self.__comans_file_tmp)
        return self.COMANS

    def MOUSE(self, command):
        file_tmp = os.getenv('GENESIS_TMP') + '/gateway.mouse'
        if os.path.exists(file_tmp) == True:
            os.unlink(file_tmp)
        # 修正：移除了 **('mode',) 错误语法
        file_handle = open(self.__com_file_tmp, 'w')
        l1 = 'COM open_entity,job=%s,type=step,name=%s,iconic=no\n' % (self.JOB(), self.STEP())
        l2 = 'AUX set_group,group=$COMANS\n'
        l3 = 'MOUSE %s\n' % command
        l4 = 'echo "$MOUSEANS "> %s\n' % file_tmp
        file_handle.writelines([
            l1,
            l2,
            l3,
            l4])
        file_handle.close()
        self.__sendCommand()
        if self.__com_status == 0:
            if os.path.exists(file_tmp):
                self.COMANS = open(file_tmp, 'r').readline().strip()
                if len(self.COMANS) == 0:
                    self.COMANS = -1

                os.unlink(file_tmp)
                return self.COMANS

    def PAUSE(self, command):
        hld = self.get_genesis_edit_hwnd()
        ctypes.windll.user32.MessageBoxW(hld, command, '提示', 0)

    def VON(self):
        # 修正：移除了 **('mode',) 错误语法
        file_handle = open(self.__com_file_tmp, 'w')
        l1 = 'VON'
        file_handle.writelines([
            l1])
        file_handle.close()
        self.__sendCommand()

    def VOF(self):
        # 修正：移除了 **('mode',) 错误语法
        file_handle = open(self.__com_file_tmp, 'w')
        l1 = 'VOF'
        file_handle.writelines([
            l1])
        file_handle.close()
        self.__sendCommand()

    def OPEN_STEP(self, step):
        # 修正：移除了 **('mode',) 错误语法
        file_handle = open(self.__com_file_tmp, 'w')
        l1 = 'COM open_entity,job=%s,type=step,name=%s,iconic=no\n' % (self.JOB(), step)
        l2 = 'AUX set_group,group=$COMANS\n'
        l3 = 'echo "$COMANS "> %s' % self.__comans_file_tmp
        file_handle.writelines([
            l1,
            l2,
            l3])
        file_handle.close()
        self.__sendCommand()
        if self.__com_status == 0:
            if os.path.exists(self.__comans_file_tmp):
                self.COMANS = open(self.__comans_file_tmp, 'r').readline().strip()
                if len(self.COMANS) == 0:
                    self.COMANS = -1

                os.unlink(self.__comans_file_tmp)
                return self.COMANS

    def INFO(self, **args):
        self.doinfo = {}
        (entity_path, data_type, parameters, serial_number, options, help, entity_type, units) = (
        '', '', '', '', '', '', '', '')
        for key, value in args.items():
            if key == 'entity_type':
                entity_type = ' -t ' + value
                continue
            if key == 'entity_path':
                entity_path = ' -e ' + value
                continue
            if key == 'data_type':
                data_type = ' -d ' + value
                continue
            if key == 'parameters':
                parameters = ' -p ' + value
                continue
            if key == 'serial_number':
                serial_number = ' -s ' + value
                continue
            if key == 'options':
                options = ' -o ' + value
                continue
            if key == 'help':
                help = ' -help '
                continue
            if key == 'units':
                units = ' units=' + value
                continue

        # 修正：将执行逻辑移出循环，并修正缩进
        flie_tmp = os.getenv('GENESIS_TMP') + '/gateway.info'
        command = 'info,out_file=' + flie_tmp + ',' + units + ',args=' + entity_type + entity_path + data_type + parameters + serial_number + options + help
        self.__gateway_com(command)
        flie = open(flie_tmp, 'r').readlines()
        os.unlink(flie_tmp)
        for arge in flie:
            regex = re.match('^set\\s+(\\S+)\\s+=\\s+(.*?)\n', arge)
            if regex != None:
                value1 = regex.group(1)
                value2 = regex.group(2)
                value3 = re.findall("('\\S*')", value2)
                if value3 != []:
                    value4 = (lambda _0: [n.replace("'", '') for n in _0])(value3)
                    if re.match('\\(', value2):
                        self.doinfo[value1] = value4
                    else:
                        self.doinfo[value1] = value4[0]
                else:
                    self.doinfo[value1] = value2
        return flie
