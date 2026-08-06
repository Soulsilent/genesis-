#!/bin/env python
import re
from genCommands import *
from genFeatures import *
import sys
import time
import os


class Genesis:
	"""top,job,step的基类"""

	def __init__(self, unit:str='mm'):
		self.unit = unit
		self.prefix = '@%#%@'
		self.blank()
		self.normalize()
		self.pid = os.getpid()
		self.tmp = 'gen_'+str(self.pid)+'.'+str(time.time())
		if 'GENESIS_DIR' in os.environ:
			self.tmpfile = os.path.join(os.environ['GENESIS_TMP'], self.tmp)
			self.tmpdir = os.environ['GENESIS_TMP']
		else:
			self.tmpfile = os.path.join('/genesis/tmp', self.tmp)
			self.tmpdir = '/genesis/tmp'

	def __del__(self):

		if os.path.isfile(self.tmpfile):
			os.unlink(self.tmpfile)
	
	def normalize(self):
		"""Normalize the path to GENESIS_EDIR, and make sure the environment is set"""
		
		if not ('GENESIS_DIR' in os.environ):
			self.error('GENESIS_DIR not set', 1)
		self.gendir = os.environ['GENESIS_DIR']
		if not ('GENESIS_DIR' in os.environ):
			self.error('GENESIS_EDIR not set', 1)
		self.edir = os.environ['GENESIS_EDIR']
		if not os.path.isdir(self.edir):
			self.edir = os.path.join(self.gendir, self.edir)
		if not os.path.isdir(self.edir):
			self.error('Cannot normalize GENESIS_EDIR', 1)
		return 0
		
	def blank(self):
		"""重置参数"""

		self.STATUS   = 0
		self.READANS  = ''
		self.COMANS   = ''
		self.PAUSANS  = ''
		self.MOUSEANS = ''
	
	def sendCmd(self, cmd, args=''):
		"""输出指令"""
		
		self.blank()
		wsp = ' '*(len(args)>0)
		cmd = self.prefix + cmd + wsp + args + '\n'
		sys.stdout.write(cmd)
		sys.stdout.flush()

		return 0
	
	@staticmethod
	def error(msg='', severity=1):
		"""错误"""

		sys.stderr.write(msg+'\n')
		if severity:
			sys.exit(severity)

	def SU_ON(self):
		""" The Genesis SU_ON command - eq. to running SU_ON in csh"""
		return self.sendCmd('SU_ON')
		
	def SU_OFF(self):
		""" Genesis SU_OFF command - eq to running SU_OFF in csh"""
		return self.sendCmd('SU_OFF')
		
	def VON(self):
		""" Genesis VON command - turns off script halting on errors- eq to running VON in csh"""
		return self.sendCmd('VON')
		
	def VOF(self):
		""" Genesis VOF command - turns on script halting on errors - eq to running VOF in csh"""
		return self.sendCmd('VOF')
		
	def PAUSE(self, msg:str):
		""" Genesis PAUSE command - pauses script with box, and allows user to interact with 
		Genesis before continuing - returns STATUS (as integer), sets class variables
		READANS and PAUSANS
			msg - string containing message to put in pause dialog box"""
		self.sendCmd(cmd='PAUSE', args=msg)
		self.STATUS = str(input())
		self.READANS = input()
		self.PAUSANS = input()
		return self.STATUS
		
	def MOUSE(self, msg, mode='p'):
		""" Genesis MOUSE command - pauses to allow user to select a location with the mouse - 
		returns STATUS as integer.  Sets class variables READANS and MOUSEANS to mouse location
			msg - message to put in dialog box
			mode - set to character 'p' or 'r'  p means to return a point, and r a rectangle (two points)"""
		self.sendCmd('MOUSE ' + mode, msg)
		self.STATUS = str(input())
		self.READANS = input()
		self.MOUSEANS = input()
		return self.STATUS
		
	def COM(self, args):
		"""com指令"""

		self.sendCmd('COM', args)
		self.STATUS = str(input())
		self.READANS = input()
		self.COMANS = self.READANS[:]

		return self.STATUS
		
	def AUX(self, args):
		""" Genesis AUX command - returns STATUS.  Sets class variables READANS 
		and COMANS, returns STATUS
			args - string containing arguments"""

		self.sendCmd('AUX', args)
		self.STATUS = str(input())
		self.READANS = input()
		self.COMANS = self.READANS[:]

		return self.STATUS

	def getInfoList(self, args:str, unit:str=''):
		"""不进行分析的原始info"""

		# 如果输入单位，则以单位为主，否则按默认单位
		if unit:
			pass
		else:
			unit = self.unit

		unitDict = {'inch': '', 'mm': 'units=mm,'}
		self.COM('info,out_file=%s,write_mode=replace,%sargs=%s' % (self.tmpfile, unitDict[unit], args))
		with open(self.tmpfile, 'r', encoding='iso-8859-15') as file:
			infoList = file.readlines()
		os.unlink(self.tmpfile)

		return infoList

	def getInfoListToDict(self, args:str, unit:str=''):
		"""将字符串列表转化为字典的info"""

		return self.parseInfoToDict(self.getInfoList(args=args, unit=unit))

	@staticmethod
	def parseInfoToDict(infoList):
		"""分析info,将字符串列表转化为字典"""

		dictAssist = {}
		for line in infoList:
			ss = line.split(' = ', 1)
			if len(ss) == 2:
				key = ss[0].strip()[4:]
				val = ss[1].strip()
				if '(' in val:
					valList = val.split("'")
					dictAssist[key] = []
					for n in range(len(valList)):
						if n % 2 == 1:
							dictAssist[key].append(valList[n].strip("'\n "))
				else:
					dictAssist[key] = val.strip("'\n ")

		return dictAssist

	def dbutil(self, *args):
		""" Runs the dbutil command with the specified arguments - returns lines from the response as
		array of strings
			args - arguments for dbutil command"""
		binary = os.path.join(self.edir, 'misc', 'dbutil')
		args = args.join()
		fd = os.popen(binary + ' '+args)
		res = fd.readlines()
		return res


class Empty:
	"""空类，用于创建空对象"""

	def __init__(self):
		pass


class Top(Genesis, TopCommands):
	"""top类"""

	def __init__(self, unit:str='mm'):
		Genesis.__init__(self, unit=unit)
		self.jobs = None
		self.currentJob = None
		self.currentStep = None

	def __getattribute__(self, item):
		"""实时获取的属性"""

		# job列表
		if item == 'jobs':
			self.__getJobs()
		# 当前job
		elif item == 'currentJob':
			self.__getCurrentJob()
		# 当前step
		elif item == 'currentStep':
			self.__getCurrentStep()

		return object.__getattribute__(self, item)

	def __getJobs(self):
		"""获取job对象字典"""

		infoAssist = self.getInfoListToDict('-t root')

		self.__dict__['jobs'] = {}
		for job in infoAssist['gJOBS_LIST']:
			self.__dict__['jobs'][job] = Job(job, unit=self.unit)

	def __getCurrentJob(self):
		"""获取当前job"""

		if 'JOB' in os.environ.keys():
			self.__dict__['currentJob'] = os.environ['JOB']
		else:
			self.__dict__['currentJob'] = ''

	def __getCurrentStep(self):
		"""当前step"""
		if 'STEP' in os.environ.keys():
			self.__dict__['currentStep'] = os.environ['STEP']
		else:
			self.__dict__['currentStep'] = ''


class Job(Genesis, JobCommands):
	"""job类"""

	def __init__(self, name, unit:str='mm'):
		Genesis.__init__(self, unit=unit)
		self.name = name
		self.matrix = Matrix(self, unit=self.unit)
		self.steps = None
		self.isChanged = None

	def __getattribute__(self, item):
		"""需要实时获取的属性"""

		if item == 'steps':
			self.__getSteps()
		elif item == 'isChanged':
			self.__getChanged()

		return object.__getattribute__(self, item)
	
	def __getSteps(self):
		"""获取step对象字典"""

		infoAssist = self.getInfoListToDict(args='-t job -e %s -d STEPS_LIST' % self.name)

		self.__dict__['steps'] = {}
		for step in infoAssist['gSTEPS_LIST']:
			self.__dict__['steps'][step] = Step(self, step, unit=self.unit)

	def __getChanged(self):
		"""job是否改变"""

		if self.getInfoListToDict(args='-t job -e %s -d IS_CHANGED' % self.name)['gIS_CHANGED'] == 'yes':
			self.__dict__['isChanged'] = True
		else:
			self.__dict__['isChanged'] = False


class Matrix(Genesis, MatrixCommands):
	"""matrix,可以用job.matrix获取"""

	def __init__(self, job, unit:str='mm'):
		Genesis.__init__(self, unit=unit)
		self.job = job
		self.name = 'matrix'
		self.row = None
		self.column = None
		self.attribute = None
		self.numberOfRows = None
		self.numberOfColumns = None
		self.numberOfLayers = None
		self.numberOfSteps = None
		self.outerSignalLayers = None
		self.innerSignalLayers = None
		self.isSingleSignalLayerBoard = None

	def __getattribute__(self, item):
		"""实时属性"""

		if item == 'row':
			self.__getRow()
		elif item == 'column':
			self.__getColumn()
		elif item == 'attribute':
			self.__getAttribute()
		elif item == 'numberOfRows':
			self.__getNumberOfRows()
		elif item == 'numberOfColumns':
			self.__getNumberOfColumns()
		elif item == 'numberOfLayers':
			self.__getNumberOfLayers()
		elif item == 'numberOfSteps':
			self.__getNumberOfSteps()
		elif item == 'outerSignalLayers':
			self.__getOuterSignalLayers()
		elif item == 'innerSignalLayers':
			self.__getInnerSignalLayers()
		elif item == 'isSingleSignalLayerBoard':
			self.__isSingleSignalLayerBoard()

		return object.__getattribute__(self, item)

	def __getRow(self):
		"""获取行信息"""

		infoAssist = self.getInfoListToDict('-t matrix -e %s/matrix -d ROW' % self.job.name)

		self.__dict__['row'] = []
		for i in range(len(infoAssist['gROWrow'])):
			assist = Empty()
			assist.row = int(infoAssist['gROWrow'][i])
			assist.type = infoAssist['gROWtype'][i]
			assist.name = infoAssist['gROWname'][i]
			assist.context = infoAssist['gROWcontext'][i]
			assist.layerType = infoAssist['gROWlayer_type'][i]
			assist.layerBaseType = infoAssist['gROWlayer_base_type'][i]
			assist.polarity = infoAssist['gROWpolarity'][i]
			assist.side = infoAssist['gROWside'][i]
			assist.drlStart = infoAssist['gROWdrl_start'][i]
			assist.drlEnd = infoAssist['gROWdrl_end'][i]
			assist.foilSide = infoAssist['gROWfoil_side'][i]
			assist.sheetSide = infoAssist['gROWsheet_side'][i]
			self.__dict__['row'].append(assist)

	def __getColumn(self):
		"""获取列信息"""

		infoAssist = self.getInfoListToDict('-t matrix -e %s/matrix -m script -d COL' % self.job.name)

		self.__dict__['column'] = []
		for i in range(len(infoAssist['gCOLcol'])):
			assist = Empty()
			assist.column = int(infoAssist['gCOLcol'][i])
			assist.type = infoAssist['gCOLtype'][i]
			assist.name = infoAssist['gCOLstep_name'][i]
			self.__dict__['column'].append(assist)

	def __getAttribute(self):
		"""获取属性信息"""

		infoAssist = self.getInfoListToDict('-t matrix -e %s/matrix -m script -d ATTR' % self.job.name)

		self.__dict__['attribute'] = []
		for i in range(len(infoAssist['gATTRname'])):
			assist = Empty()
			assist.value = infoAssist['gATTRval'][i]
			assist.name = infoAssist['gATTRname'][i]
			self.__dict__['row'].append(assist)

	def __getNumberOfRows(self):
		"""获取行数"""

		infoAssist = self.getInfoListToDict('-t matrix -e %s/matrix -d NUM_ROWS' % self.job.name)

		self.__dict__['numberOfRows'] = int(infoAssist['gNUM_ROWS'])

	def __getNumberOfColumns(self):
		"""获取列数"""

		infoAssist = self.getInfoListToDict('-t matrix -e %s/matrix -d NUM_COLS' % self.job.name)

		self.__dict__['numberOfColumns'] = int(infoAssist['gNUM_COLS'])

	def __getNumberOfLayers(self):
		"""获取层数"""

		infoAssist = self.getInfoListToDict('-t matrix -e %s/matrix -d NUM_LAYERS' % self.job.name)

		self.__dict__['numberOfLayers'] = int(infoAssist['gNUM_LAYERS'])

	def __getNumberOfSteps(self):
		"""获取步骤数"""

		infoAssist = self.getInfoListToDict('-t matrix -e %s/matrix -d NUM_STEPS' % self.job.name)

		self.__dict__['numberOfSteps'] = int(infoAssist['gNUM_STEPS'])

	def __getOuterSignalLayers(self):
		"""获取外层"""

		signalLayers = self.returnRows(context='board', layerType='signal')
		if len(signalLayers) == 0:
			self.__dict__['outerSignalLayers'] = []
		elif len(signalLayers) == 1:
			self.__dict__['outerSignalLayers'] = [signalLayers[0]]
		else:
			self.__dict__['outerSignalLayers'] = [signalLayers[0], signalLayers[-1]]

	def __getInnerSignalLayers(self):
		"""获取内层"""

		signalLayers = self.returnRows(context='board', layerType='signal')
		if len(signalLayers) <= 2:
			self.__dict__['innerSignalLayers'] = []
		else:
			signalLayers.pop(0)
			signalLayers.pop(-1)
			self.__dict__['innerSignalLayers'] = signalLayers.copy()

	def __isSingleSignalLayerBoard(self):
		"""是否为单面板"""

		signalLayers = self.returnRows(context='board', layerType='signal')
		if len(signalLayers) == 1:
			self.__dict__['isSingleSignalLayerBoard'] = True
		else:
			self.__dict__['isSingleSignalLayerBoard'] = False


class Step(Genesis, StepCommands):
	"""step类"""
	
	def __init__(self, job, name, unit:str='mm'):
		Genesis.__init__(self, unit=unit)
		self.job = job
		self.name = name
		self.group = None
		self.layers = None
		self.profileLimits = None
		self.srLimits = None
		self.sr = None
		self.workLayer = None
		self.affectedLayers = None
		self.selectedCounts = None
		self.currentUnit = None
		
	def COM(self, args):
		"""设置能影响到当前窗口的COM"""

		if self.group:
			self.AUX('set_group,group='+self.group)
		self.sendCmd('COM', args)
		self.STATUS = str(input())
		self.READANS = input()
		self.COMANS = self.READANS[:]

		return self.STATUS

	def __getattribute__(self, item):
		"""动态更新的属性"""

		# 层对象字典
		if item == 'layers':
			self.__getLayers()
		# profile范围
		elif item == 'profileLimits':
			self.__getProfileLimits()
		# sr范围
		elif item == 'srLimits':
			self.__getSrLimits()
		# sr
		elif item == 'sr':
			self.__getSr()
		# 工作层
		elif item == 'workLayer':
			self.__getWorkLayer()
		# 影响层
		elif item == 'affectedLayers':
			self.__getAffectedLayers()
		# 影响层
		elif item == 'selectedCounts':
			self.__getSelectedCounts()
		# 当前单位
		elif item == 'currentUnit':
			self.__getCurrentUnit()

		return object.__getattribute__(self, item)

	def __getProfileLimits(self):
		"""获取Profile信息"""

		infoAssist = self.getInfoListToDict('-t step -e %s/%s -d PROF_LIMITS' % (self.job.name, self.name))

		self.__dict__['profileLimits'] = Empty()
		self.__dict__['profileLimits'].xMin = float(infoAssist['gPROF_LIMITSxmin'])
		self.__dict__['profileLimits'].yMin = float(infoAssist['gPROF_LIMITSymin'])
		self.__dict__['profileLimits'].xMax = float(infoAssist['gPROF_LIMITSxmax'])
		self.__dict__['profileLimits'].yMax = float(infoAssist['gPROF_LIMITSymax'])
		self.__dict__['profileLimits'].xSize = self.__dict__['profileLimits'].xMax - self.__dict__['profileLimits'].xMin
		self.__dict__['profileLimits'].ySize = self.__dict__['profileLimits'].yMax - self.__dict__['profileLimits'].yMin
		self.__dict__['profileLimits'].xCenter = self.__dict__['profileLimits'].xMin + self.__dict__['profileLimits'].xSize / 2
		self.__dict__['profileLimits'].yCenter = self.__dict__['profileLimits'].yMin + self.__dict__['profileLimits'].ySize / 2

	def __getSrLimits(self):
		"""获取SR范围"""

		infoAssist = self.getInfoListToDict('-t step -e %s/%s -d SR_LIMITS' % (self.job.name, self.name))

		self.__dict__['srLimits'] = Empty()
		self.__dict__['srLimits'].xMin = float(infoAssist['gSR_LIMITSxmin'])
		self.__dict__['srLimits'].yMin = float(infoAssist['gSR_LIMITSymin'])
		self.__dict__['srLimits'].xMax = float(infoAssist['gSR_LIMITSxmax'])
		self.__dict__['srLimits'].yMax = float(infoAssist['gSR_LIMITSymax'])
		self.__dict__['srLimits'].rightBorder = self.profileLimits.xMax - self.__dict__['srLimits'].xMax
		self.__dict__['srLimits'].leftBorder = self.__dict__['srLimits'].xMin - self.profileLimits.xMin
		self.__dict__['srLimits'].upBorder = self.profileLimits.yMax - self.__dict__['srLimits'].yMax
		self.__dict__['srLimits'].downBorder = self.__dict__['srLimits'].yMin - self.profileLimits.yMin

	def __getSr(self):
		"""获取SR信息"""

		infoAssist = self.getInfoListToDict('-t step -e %s/%s -d SR' % (self.job.name, self.name))

		self.__dict__['sr'] = []
		for i in range(len(infoAssist['gSRstep'])):
			assist = Empty()
			assist.step = infoAssist['gSRstep'][i]
			assist.anchorPoint = Point(x=float(infoAssist['gSRxa'][i]), y=float(infoAssist['gSRya'][i]))
			assist.dX = float(infoAssist['gSRdx'][i])
			assist.dY = float(infoAssist['gSRdy'][i])
			assist.nX = int(infoAssist['gSRnx'][i])
			assist.nY = int(infoAssist['gSRny'][i])
			assist.angle = 360 - float(infoAssist['gSRangle'][i])
			assist.mirror = infoAssist['gSRmirror'][i]

			self.__dict__['sr'].append(assist)
	
	def __getLayers(self):
		"""获取层对象"""

		infoAssist = self.getInfoListToDict('-t step -e %s/%s -d LAYERS_LIST' % (self.job.name, self.name))

		self.__dict__['layers'] = {}
		for layerName in infoAssist['gLAYERS_LIST']:
			self.__dict__['layers'][layerName] = Layer(self, layerName)

	def __getWorkLayer(self):
		"""获取工作层"""

		self.COM('get_work_layer')
		self.__dict__['workLayer'] = self.COMANS

	def __getAffectedLayers(self):
		"""获取影响层"""

		self.COM('get_affect_layer')
		self.__dict__['affectedLayers'] = self.COMANS.split()

	def __getSelectedCounts(self):
		"""选中的数量"""

		self.COM('get_select_count')
		self.__dict__['selectedCounts'] = int(self.COMANS)

	def __getCurrentUnit(self):
		"""获取当前单位"""

		self.COM('get_units')
		self.__dict__['currentUnit'] = self.COMANS


class Layer:
	"""layer类,可通过step.layers调用"""

	def __init__(self, step, name):
		self.step = step
		self.name = name
		self.job = self.step.job
		self.attribute = None
		self.baseType = None
		self.context = None
		self.features = None
		self.selectedFeatures = None
		self.limits = None
		self.toolRowNumber = None
		self.tool = None
		self.featureHist = None
		self.symbolHist = None
		self.toolUser = None

	def __getattribute__(self, item):
		"""动态获取属性"""

		if item == 'attribute':
			self.__getAttribute()
		elif item == 'baseType':
			self.__getBaseType()
		elif item == 'context':
			self.__getContext()
		elif item == 'features':
			self.__getFeatures()
		elif item == 'selectedFeatures':
			self.__getSelectedFeatures()
		elif item == 'limits':
			self.__getLimits()
		elif item == 'toolRowNumber':
			self.__getToolRowNumber()
		elif item == 'tool':
			self.__getTool()
		elif item == 'featureHist':
			self.__getFeatureHist()
		elif item == 'symbolHist':
			self.__getSymbolHist()
		elif item == 'toolUser':
			self.__getToolUser()

		return object.__getattribute__(self, item)

	def __getAttribute(self):
		"""获取属性信息"""

		infoAssist = self.step.getInfoListToDict(args='-t layer -e %s/%s/%s -d ATTR' % (self.job.name, self.step.name, self.name))

		self.__dict__['attribute'] = []
		for i in range(len(infoAssist['gATTRname'])):
			assist = Empty()
			assist.value = infoAssist['gATTRval'][i]
			assist.name = infoAssist['gATTRname'][i]
			self.__dict__['row'].append(assist)

	def __getBaseType(self):

		infoAssist = self.step.getInfoListToDict(args='-t layer -e %s/%s/%s -d BASE_TYPE' % (self.job.name, self.step.name, self.name))

		self.__dict__['baseType'] = infoAssist['gBASE_TYPE']

	def __getContext(self):
		"""context"""

		infoAssist = self.step.getInfoListToDict(args='-t layer -e %s/%s/%s -d CONTEXT' % (self.job.name, self.step.name, self.name))

		self.__dict__['context'] = infoAssist['gCONTEXT']

	def __getLimits(self):
		"""范围"""

		infoAssist = self.step.getInfoListToDict(args='-t layer -e %s/%s/%s -d LIMITS' % (self.job.name, self.step.name, self.name))

		self.__dict__['limits'] = Empty()
		self.__dict__['limits'].xMin = float(infoAssist['gLIMITSxmin'])
		self.__dict__['limits'].yMin = float(infoAssist['gLIMITSymin'])
		self.__dict__['limits'].xMax = float(infoAssist['gLIMITSxmax'])
		self.__dict__['limits'].yMax = float(infoAssist['gLIMITSymax'])
		self.__dict__['limits'].xCenter = float(infoAssist['gLIMITSxcenter'])
		self.__dict__['limits'].yCenter = float(infoAssist['gLIMITSycenter'])
		self.__dict__['limits'].xSize = self.__dict__['limits'].xMax - self.__dict__['limits'].xMin
		self.__dict__['limits'].ySize = self.__dict__['limits'].yMax - self.__dict__['limits'].yMin

	def __getFeatureHist(self):
		"""feature统计"""

		infoAssist = self.step.getInfoListToDict(args='-t layer -e %s/%s/%s -d FEAT_HIST' % (self.job.name, self.step.name, self.name))

		self.__dict__['featureHist'] = Empty()
		self.__dict__['featureHist'].line = int(infoAssist['gFEAT_HISTline'])
		self.__dict__['featureHist'].pad = int(infoAssist['gFEAT_HISTpad'])
		self.__dict__['featureHist'].surface = int(infoAssist['gFEAT_HISTsurf'])
		self.__dict__['featureHist'].arc = int(infoAssist['gFEAT_HISTarc'])
		self.__dict__['featureHist'].text = int(infoAssist['gFEAT_HISTtext'])
		self.__dict__['featureHist'].total = int(infoAssist['gFEAT_HISTtotal'])

	def __getFeatures(self):
		"""所有物件信息"""

		self.__dict__['features'] = self.parseFeatureInfo(infoList=self.step.getInfoList(args='-t layer -e %s/%s/%s -d FEATURES -o feat_index' % (self.job.name, self.step.name, self.name)))

	def __getSelectedFeatures(self):
		"""选中的物件信息"""

		self.__dict__['selectedFeatures'] = self.parseFeatureInfo(infoList=self.step.getInfoList(args='-t layer -e %s/%s/%s -d FEATURES -o feat_index+select' % (self.job.name, self.step.name, self.name)))

	def __getToolRowNumber(self):
		"""钻孔表行数"""

		infoAssist = self.step.getInfoListToDict(args='-t layer -e %s/%s/%s -d NUM_TOOL' % (self.job.name, self.step.name, self.name))

		self.__dict__['toolRowNumber'] = int(infoAssist['gNUM_TOOL'])

	@staticmethod
	def parseFeatureInfo(infoList:list):
		"""分析feature"""

		featureObject = Empty()
		featureObject.lines = []
		featureObject.arcs = []
		featureObject.pads = []
		featureObject.surfaces = []
		featureObject.texts = []
		featureObject.bars = []

		pat_line = re.compile(r'^#[0-9]+\s+#L')
		pat_arc = re.compile(r'^#[0-9]+\s+#A')
		pat_pad = re.compile(r'^#[0-9]+\s+#P')
		pat_surface = re.compile(r'^#[0-9]+\s+#S')
		pat_text = re.compile(r'^#[0-9]+\s+#T')
		pat_bar = re.compile(r'^#[0-9]+\s+B')
		for line in infoList:
			line = line.strip()
			if pat_line.search(line):
				featureObject.lines.append(Line(line))
			elif pat_arc.search(line):
				featureObject.arcs.append(Arc(line))
			elif pat_pad.search(line):
				featureObject.pads.append(Pad(line))
			elif pat_surface.search(line):
				featureObject.surfaces.append(Surface(line))
			elif pat_text.search(line):
				featureObject.texts.append(Text(line))
			elif pat_bar.search(line):
				featureObject.bars.append(Barcode(line))

		return featureObject

	def __getTool(self):
		"""钻孔表"""

		infoAssist = self.step.getInfoListToDict('-t layer -e %s/%s/%s -d TOOL' % (self.job.name, self.step.name, self.name), unit='mm')

		self.__dict__['tool'] = []
		for i in range(self.toolRowNumber):
			assist = Empty()
			assist.number = int(infoAssist['gTOOLnum'][i])
			assist.count = int(infoAssist['gTOOLcount'][i])
			assist.shape = infoAssist['gTOOLshape'][i]
			assist.type = infoAssist['gTOOLtype'][i]
			assist.type2 = infoAssist['gTOOLtype2'][i]
			assist.minTol = float(infoAssist['gTOOLmin_tol'][i])
			assist.maxTol = float(infoAssist['gTOOLmax_tol'][i])
			assist.finishSize = float(infoAssist['gTOOLfinish_size'][i])
			assist.drillSize = float(infoAssist['gTOOLdrill_size'][i])
			assist.bit = infoAssist['gTOOLbit'][i]
			assist.slotLength = float(infoAssist['gTOOLslot_len'][i])
			assist.userDes = infoAssist['gTOOLuser_des'][i]
			self.__dict__['tool'].append(assist)

	def __getToolUser(self):
		"""获取工具使用者"""

		infoAssist = self.step.getInfoListToDict('-t layer -e %s/%s/%s -d TOOL_USER' % (self.job.name, self.step.name, self.name))
		self.__dict__['toolUser'] = infoAssist['gTOOL_USER']

	def __getSymbolHist(self):
		"""symbol统计"""

		infoAssist = self.step.getInfoListToDict('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job.name, self.step.name, self.name))

		self.__dict__['symbolHist'] = []
		for i in range(len(infoAssist['gSYMS_HISTsymbol'])):
			assist = Empty()
			assist.symbol = infoAssist['gSYMS_HISTsymbol'][i]
			assist.line = int(infoAssist['gSYMS_HISTline'][i])
			assist.pad = int(infoAssist['gSYMS_HISTpad'][i])
			assist.arc = int(infoAssist['gSYMS_HISTarc'][i])
			self.__dict__['symbolHist'].append(assist)




