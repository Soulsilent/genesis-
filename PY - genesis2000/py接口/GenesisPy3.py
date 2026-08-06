#!/usr/bin/env python
#coding:utf-8

#__作者__ = "毛毛雨qq:5970356"
#__日期__ = "2021.01.06"
#__版本__ = "版本1.0 应用python3"
__author__  = "maomaoyu qq:5970356"
__date__    = "2021.01.06"
__version__ = "Revision: 1.0 apply to python3"


import re,os,sys

class Genesis():
    GENESIS_DIR = ""
    GENESIS_EDIR = ""
    GENESIS_TMP = ""
    STATUS = -1
    COMANS = ""	
    MOUSEANS = ""
    PAUSANS = ""
    doinfo = {}



    def __init__(self):
        self.GENESIS_DIR = os.getenv('GENESIS_DIR')
        self.GENESIS_EDIR = os.getenv('GENESIS_EDIR')
        self.GENESIS_TMP = os.getenv('GENESIS_TMP')
	
    def __blank(self):
        self.STATUS = -1
        self.COMANS = ""		
        self.MOUSEANS = ""
        self.PAUSANS = ""


    def __write(self,command):
        DIR_PREFIX = '@%#%@'
        sys.stdout.write(DIR_PREFIX + command + "\n")
        sys.stdout.flush()

    def __read(self):
        value = input()
        return(value)
        
    def JOB(self):
        return str(os.getenv('JOB'))

    def STEP(self):
        return str(os.getenv('STEP'))       
	
    def COM(self,command):
        self.__blank()
        self.__write("COM " + command)
        self.STATUS = self.__read()
        self.COMANS = self.__read()
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
        self.__write("VON")
    
    def VOF(self):
        self.__write("VOF")
    
    def SU_ON(self):
        self.__write("SU_ON")

    def SU_OFF(self):
        self.__write("SU_OFF")

    def MOUSE(self,command):
        self.__blank()
        self.__write("MOUSE " + command)
        self.STATUS = self.__read()
        self.COMANS = self.__read()
        value = self.__read()
        self.MOUSEANS = value.split()
        ##return value
        return self.MOUSEANS
        

    def PAUSE(self,command):
        self.__blank()
        self.__write("PAUSE " + command)
        self.STATUS = self.__read()
        self.COMANS = self.__read()
        self.READANS = self.__read()
        return self.PAUSANS


    # ggg=g.DO_INFO("-t step -e %s/panel -m script -d PROF_LIMITS"%(g.JOB()),units = 'inch')
    # print(self.doinfo['gPROF_LIMITSxmin'])
    # print(self.doinfo['gPROF_LIMITSymin'])
    # print(self.doinfo['gPROF_LIMITSxmax'])
    # print(self.doinfo['gPROF_LIMITSymax'])
    # print(self.doinfo)
    def DO_INFO(self,command,*,units="units=mm"):
        self.doinfo = {}

        flie_tmp = os.getenv("GENESIS_TMP") + "/genesis_python.tmp"
        
        ##units = "units=mm"
        if units == "inch":
            units = "units=inch"
        else:
            units = "units=mm"
                
        args = "info,out_file=" + flie_tmp + "," + units +",args=" + command
        self.COM(args)


        flie = open(flie_tmp,'r').readlines()
        #os.unlink(flie_tmp)

        #self.doinfo['all_data'] = flie  

        for arge in flie:
            regex = re.match("^set\s+(\S+)\s+=\s+(.*?)\n",arge)

            if regex != None:
                    value1 = regex.group(1)
                    value2 = regex.group(2)
                    value3 = re.findall("('\S*')",value2)
                                
                    if value3 != []:
                        
                        value4 = [n.replace("'","") for n in value3]
                        if re.match("\(",value2):
                            self.doinfo[value1] = value4
                        else:
                            self.doinfo[value1] = value4[0]
                    else:     
                        self.doinfo[value1] = value2
                                      
        return flie  #返回调整后的内容



    # ggg=self.INFO(units = 'mm', entity_type ='step',entity_path = g.JOB()+"/panel",data_type = 'PROF_LIMITS')
    # print(self.doinfo['gPROF_LIMITSxmin'])
    # print(self.doinfo['gPROF_LIMITSymin'])
    # print(self.doinfo['gPROF_LIMITSxmax'])
    # print(self.doinfo['gPROF_LIMITSymax'])
    # #print(ggg)
    def INFO(self,**args):
        self.doinfo = {}
        entity_path, data_type, parameters, serial_number, options, help, entity_type, units = ("","","","","","","","")
        for key, value in args.items():
            if key == "entity_type":
                entity_type = " -t "+ value
            elif key ==  "entity_path":
                entity_path = " -e "+ value
            elif key ==  "data_type":    
                data_type = " -d "+ value
            elif key ==  "parameters":     
                parameters = " -p "+ value
            elif key ==  "serial_number":   
                serial_number  = " -s "+ value
            elif key ==  "options":       
                options = " -o "+ value            
            elif key ==  "help":   
                help= " -help "
            elif key ==  "units":    
                units =" units="+ value
        flie_tmp = os.getenv("GENESIS_TMP") + "/genesis_python.tmp"
        command = "info,out_file=" + flie_tmp + "," + units +",args=" + entity_type +entity_path +data_type + parameters +serial_number +options +help
        self.COM(command)

        flie = open(flie_tmp,'r').readlines()
        os.unlink(flie_tmp)

        #self.doinfo['all_data'] = flie  
        for arge in flie:
            regex = re.match("^set\s+(\S+)\s+=\s+(.*?)\n",arge) 
            if regex != None:
                    value1 = regex.group(1)
                    value2 = regex.group(2)
                    value3 = re.findall("('\S*')",value2)  
                                                 
                    if value3 != []:   
                        value4 = [n.replace("'","") for n in value3]
                        if re.match("\(",value2):
                            self.doinfo[value1] = value4
                        else:
                            self.doinfo[value1] = value4[0]
                    else:
                        if value2 =="()":
                            self.doinfo[value1] = ""
                        else:
                            self.doinfo[value1] = value2        
        return flie  #返回调整后的内容

    #得到layer 列表, 不返回空层
    def get_layers(self)->list:
        self.INFO(units = 'mm', entity_type = 'matrix',entity_path = "%s/matrix"%(self.JOB()))
        #去掉空层名
        layer_list=[]
        for _layer in self.doinfo["gROWname"]:
            if _layer !='':
                layer_list.append(_layer)        
        return layer_list
    # 得到step列表
    def get_steps(self) -> list:
        self.INFO(units='mm', entity_type='job', entity_path="%s/STEPS_LIST" % (self.JOB()))
        step_list = []
        for _step in self.doinfo["gSTEPS_LIST"]:
            step_list.append(_step)
            if _step == '':
             return None
        return step_list



    #打开step
    def open_step(self,step_name):
        self.COM("open_entity,job=%s,type=step,name=%s,iconic=no"%(self.JOB(),step_name))        
        self.AUX("set_group,group=%s"%(self.COMANS))
        return self.COMANS




    #得到拼板层次名称与数量
    #递归遍历所有panel 下的pcs
    #用法  setp_level(["panel"]) 必须带[]  "panel"
    __setp_dict={}
    def setp_level(self,step=[])-> dict:
        for  step_name in step:
            self.INFO(entity_type = "step",entity_path = "%s/%s"%(self.JOB(),step_name),data_type = 'REPEAT')
            next_set=self.doinfo["gREPEATstep"]		
            #存入字典
            self.__setp_dict[step_name] = self.__setp_dict.get(step_name, 0) + 1
            if next_set !="": 
                self.setp_level(next_set)

        return(self.__setp_dict)	




    #得到拼板数量
    #用法  setp_level(["panel"]) 必须带[]  "panel"
    def pcs_count(self,step=[])->int:
        
        for  step_name in step:
            self.INFO(entity_type = "step",entity_path = "%s/%s"%(self.JOB(),step_name),data_type = 'REPEAT')
            next_set=self.doinfo["gREPEATstep"]		
            #存入字典
            self.__setp_dict[step_name] = self.__setp_dict.get(step_name, 0) + 1
            if next_set !="": 
                self.pcs_count(next_set)

        pnl=self.__setp_dict
        xs=0
        for key in pnl.keys():
            self.INFO(entity_type = "step",entity_path = "%s/%s"%(self.JOB(),key),data_type = 'REPEAT')
            if self.doinfo["gREPEATstep"]=="":
                xs=xs + int(pnl[key])

        return(xs)	

    # 删除料号
    def del_job(self,job):
        self.VOF()
        self.COM('close_job,job=%s'%job)
        self.COM('matrix_page_close,job=%s,matrix=matrix'%job)
        self.COM('close_form,job=%s'%job)
        self.COM('close_flow,job=%s'%job)
        self.VON()

        self.COM('delete_entity,job=,type=job,name=%s'%job)
        self.COM('get_user_name')
        self.COM('disp_on')
        self.COM('close_form,job=%s'%job)
        self.COM('close_flow,job=%s'%job)

        # 判断料号是否存在
    # def exists_job(self,job_name):
    #         self.INFO(units='mm', entity_type='job',
    #                 entity_path ='%s'%job_name,
    #                 data_type ='EXISTS')
    #         msg = g.doinfo['gEXISTS']
    #         return msg

    # ==================== 涨缩计算功能 ====================

    def get_scale(self, base_value=100000, **kwargs):
        """
        获取缩放比例（涨缩值 → 缩放比例）
        逆推逻辑：scale * 10 加到基准值上
        a = 1.0003
        b = 1.00095
        result = g.get_scale(x=a, y=b)
        result1 = g.get_scale_value(x=a, y=b)
        print(result1)
        """
        def reverse_calculate(target_scale):
            if target_scale is None:
                return 1.0
            if target_scale == 0:
                return 1.0
            
            scaled_value = base_value + target_scale * 10
            return scaled_value / 100000

        result = {}
        if 'x' in kwargs and kwargs['x'] is not None:
            result['x'] = reverse_calculate(kwargs['x'])
        if 'y' in kwargs and kwargs['y'] is not None:
            result['y'] = reverse_calculate(kwargs['y'])
        return result

    def get_scale_value(self, base_value=100000, **kwargs):
        """
        获取涨缩值（缩放比例 → 涨缩值）
        严格遵循 Perl/Shell 逻辑，取消智能判断
        """
        def forward_calculate(scale_factor):
            if scale_factor is None:
                return 0

            # 1. 取整 (对应 echo "scale=0; ... * 100000" | bc | awk)
            inputscale = int(scale_factor * 100000)
            
            # 2. 严格套用 Perl 条件分支
            if inputscale > base_value:
                result = (inputscale - base_value) * 0.1
            elif inputscale < base_value:
                result = -(base_value - inputscale) * 0.1
            else:
                result = 0
            
            # 3. 保留3位小数 (对应 scale=3)
            return round(result, 3)

        result = {}
        if 'x' in kwargs and kwargs['x'] is not None:
            result['x'] = forward_calculate(kwargs['x'])
        if 'y' in kwargs and kwargs['y'] is not None:
            result['y'] = forward_calculate(kwargs['y'])
        return result

    # ==================== 绘图辅助功能 ====================
    def add_line(self, xs, ys, xe, ye, symbol='r3', polarity='positive'):
        """
        在 Genesis 中绘制一条直线。

        参数:
            xs, ys: 起点坐标 (Start X, Start Y)
            xe, ye: 终点坐标 (End X, End Y)
            symbol: 线宽/线型，默认 'r3'
            polarity: 极性，默认 'positive'
        """
        # 1. 确保坐标是数字（防止传入字符串导致计算错误）
        xs = float(xs)
        ys = float(ys)
        xe = float(xe)
        ye = float(ye)

        # 2. 组装 add_line 命令字符串
        # 注意：这里使用了 f-string 格式化，保持与你之前的指令风格一致
        cmd = f"add_line,attributes=no,xs={xs},ys={ys},xe={xe},ye={ye},symbol={symbol},polarity={polarity}"

        # 3. 调用类内部的 COM 方法发送指令
        self.COM(cmd)

    def outPutDxf(
            self,
            job: str,  # 作业名称 (必填)
            step: str,  # Step名称 (必填)
            layers: str,  # 图层名称，多个用 | 分隔 (必填)
            dirPath: str = '',  # 输出目录路径
            prefix: str = '',  # 输出文件名前缀
            suffix: str = '.dxf',  # 输出文件名后缀
            mirrors: str = 'no',  # 镜像设置
            xscale: float = 1,  # X轴缩放比例
            yscale: float = 1,  # Y轴缩放比例
            # --- Break & Scale ---
            break_sr: str = 'yes',  # Break S&R (打散Step & Repeater)
            break_symbols: str = 'yes',  # Break symbols (打散符号)
            break_arc: str = 'yes',  # Break arcs (打散圆弧)
            scale_mode: str = 'all',  # Scale mode (缩放模式: all / Scale features / Unscale targets)
            surface_mode: str = 'fill',  # Surfaces mode (表面模式: fill / contour)
            min_brush: float = 25.4,  # Minimal brush (最小笔刷宽度，单位跟随units)
            # --- Units & Options ---
            units: str = 'mm',  # Units (输出单位: mm / inch)
            x_anchor: float = 0,  # X Anchor (X轴锚点)
            y_anchor: float = 0,  # Y Anchor (Y轴锚点)
            x_offset: float = 0,  # X Offset (X轴偏移)
            y_offset: float = 0,  # Y Offset (Y轴偏移)
            line_units: str = 'mm',  # Line Units (线宽单位: mm / inch)
            override_online: str = 'no',  # Override Online (覆盖在线参数)
            Pad_as_Circle: str = 'no',  # Pad as Circle (焊盘转圆)
            draft: str = 'no',  # Draft Mode (模式)
            contour_to_hatch: str = 'no',  # Contour to HATCH (轮廓转填充)
            pad_outline: str = 'no',  # Rectangle/Square Pads to Outline (矩形/方形焊盘转外框)
            output_files: str = 'multiple',  # Output Files (输出文件模式: multiple / single)
            file_ver: str = 'autocad2002'  # File Version (DXF文件版本，仅autocad2002)
    ):
        """
        输出 DXF (适配 GenesisPy3.py 接口风格)
        参数完全对应 Genesis Output 弹窗，无 UI
        """
        # 1. 重置图层设置
        self.COM('output_layer_reset')

        # 2. 设置每个图层的参数
        for layer in layers.split('|'):
            self.COM(
                f'output_layer_set,layer={layer},angle=0,mirror={mirrors},'
                f'x_scale={xscale},y_scale={yscale},comp=0,polarity=positive,'
                f'setupfile=,setupfiletmp=,line_units={line_units},gscl_file=,step_scale=no'
            )

        # 3. 组装并执行输出命令
        params = {
            'job': job, 'step': step, 'format': 'DXF', 'dir_path': dirPath,
            'prefix': prefix, 'suffix': suffix,
            'break_sr': break_sr, 'break_symbols': break_symbols, 'break_arc': break_arc,
            'scale_mode': scale_mode, 'surface_mode': surface_mode, 'min_brush': min_brush,
            'units': units, 'x_anchor': x_anchor, 'y_anchor': y_anchor,
            'x_offset': x_offset, 'y_offset': y_offset, 'line_units': line_units,
            'override_online': override_online, 'pads_2circles': Pad_as_Circle, 'draft': draft,
            'contour_to_hatch': contour_to_hatch, 'pad_outline': pad_outline,
            'output_files': output_files, 'file_ver': file_ver
        }
        # 使用字典拼接参数，保持代码整洁，与 GenesisPy3.py 中的 add_line 风格一致
        self.COM('output,' + ','.join(f'{k}={v}' for k, v in params.items()))

