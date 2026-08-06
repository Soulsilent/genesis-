from genesisGeometry import *
import math


class Feature:
	"""基类"""
	
	def __init__(self, line):
		self.line = line.strip()
		self.getAttributes()
	
	def getAttributes(self):
		"""获取feature属性"""

		# 获取序号和feature
		ss = self.line.split(';')
		ssAssist = ss[0].split('#')
		self.line = ssAssist[2]
		self.index = int(ssAssist[1].strip())

		# 获取属性
		self.attributes = {}
		if len(ss) > 1:
			for attr in ss[1].split(','):
				if '=' in attr:
					name,val = attr.split('=')
				else:
					name,val = (attr, '1')
				self.attributes[name] = val

	def copy(self):
		"""复制"""

		return copy.deepcopy(self)
		
	def __repr__(self):
		STR = '<Feature.'+self.shape+' Object>'
		return STR


class Pad(Feature):
	"""This class defines an object which describes a Pad.  It is subclassed 
	from Feature.  It gets passed the line from the INFO command (-d FEATURES)
		Variables in Pad (access by class.<var>)
			x, y - location
			symbol - Symbol used in drawing line
			polarity - Polarity of line
			dcode - dcode of symbol used
			rotation - rotation in degrees of Pad
			mirror - yes if mirrored"""
			
	def __init__(self, line):
		super().__init__(line)
		self.shape = 'Pad'
		self.lookups = {
			'polarity': {'P':'positive', 'N':'negative'},
			'Y/N':   {'Y': 'yes', 'N': 'no'},
			}
		self.parse()
		
	def parse(self):
		ss = self.line.split()
		if len(ss) < 8:
			return 0
		self.geometry = Point(x=float(ss[1]), y=float(ss[2]))
		self.symbol   = ss[3]
		self.polarity = self.lookups['polarity'][ss[4]]
		self.dcode    = str(ss[5])
		self.rotation = str(ss[6])
		self.mirror   = self.lookups['Y/N'][ss[7]]


class Line(Feature):
	"""线"""
		
	def __init__(self, line):
		super().__init__(line)
		self.shape = 'Line'
		self.lookups = {'polarity':{'P':'positive', 'N':'negative'}}
		self.parse()
		
	def parse(self):
		ss = self.line.split()
		if len(ss) < 8:
			return 0
		self.geometry = Segment(startPoint=Point(x=float(ss[1]), y=float(ss[2])), endPoint=Point(x=float(ss[3]), y=float(ss[4])))
		self.symbol = ss[5]
		self.polarity = self.lookups['polarity'][ss[6]]
		self.dcode = str(ss[7])


class Surface(Feature):
	"""铜皮"""

	def __init__(self, line):
		super().__init__(line)
		self.shape = 'Surface'


class Arc(Feature):
	"""圆弧"""
	def __init__(self, line):
		super().__init__(line)
		self.shape = 'Arc'
		self.lookups = {'polarity': {'P':'positive', 'N':'negative'}, 'direction': {'Y': 'CW', 'N': 'CCW'}}
		self.parse()
		
	def parse(self):
		ss = self.line.split()
		if len(ss) < 11:
			return 0
		self.geometry = Camber(startPoint=Point(x=float(ss[1]), y=float(ss[2])), endPoint=Point(x=float(ss[3]), y=float(ss[4])), centerPoint=Point(x=float(ss[5]), y=float(ss[6])), direction=self.lookups['direction'][ss[10]])
		self.symbol = ss[7]
		self.polarity = self.lookups['polarity'][ss[8]]
		self.dcode = ss[9]


class Text(Feature):
	"""字"""
			
	def __init__(self, line):
		super().__init__(line)
		self.shape = 'Text'
		self.lookups = {
			'polarity': {'P':'positive', 'N':'negative'},
			'Y/N':   {'Y': 'yes', 'N': 'no'},
			}
		self.parse()
		
	def parse(self):
		ss = self.line.split()
		if len(ss) < 12:
			return 0
		self.geometry = Point(x=float(ss[1]), y=float(ss[2]))
		self.fontName     = ss[3]
		self.polarity = self.lookups['polarity'][ss[4]]
		self.angle = 360 - float(ss[5])
		self.mirror   = self.lookups['Y/N'][ss[6]]
		self.xSize    = float(ss[7]) * 1000
		self.ySize    = float(ss[8]) * 1000
		self.width  = float(ss[9]) * 304.8
		self.text     = ss[10].strip("'")
		self.version  = str(ss[11])


class Barcode(Feature):
	"""This class defines an object which describes a Barcode.  It is subclassed 
	from Feature.  It gets passed the line from the INFO command (-d FEATURES)
		Variables in Barcode Feature (access by class.<var>)
			x, y - location
			barcode - barcode type
			font - font name for under code
			polarity - Polarity of line
			rotation - rotation in degrees
			constant - Don't know
			width - mils of code in x direction
			heigt - mils of code in the y direction
			full_ascii - don't know
			cksum - checksum?
			invert_bg - invert the barcode yes/no
			add_text - add text to bottom of code yes/no
			text_loc - top/bot of the code
			text - text encoded in the barcode"""
			
	def __init__(self, line):
		super().__init__(line)
		self.shape = 'Barcode'
		self.lookups = {
			'polarity': {'P':'positive', 'N':'negative'},
			'boolean': {'Y':1,'N':0,  'yes':1,'no':0,  'y':1,'n':0,  '1':1,'0':0},
			'top/bot': {'T':'top','B':'bottom','top':'top','bot':'bottom'},
			}
		self.parse()
		
	def parse(self):
		ss = self.line.split()
		if len(ss) < 12: return 0
		self.x        = str(ss[1])
		self.y        = str(ss[2])
		self.barcode  = ss[3]
		self.font     = ss[4]
		self.polarity = self.lookups['polarity'][ss[5]]
		self.rotation = str(ss[6])
		self.constant = ss[7]
		self.width    = str(ss[8])
		self.height   = str(ss[9])
		self.full_ascii  = self.lookups['boolean'][ss[10]]
		self.cksum       = self.lookups['boolean'][ss[11]]
		self.invert_bg   = self.lookups['boolean'][ss[12]]
		self.add_text    = self.lookups['boolean'][ss[13]]
		self.text_loc    = self.lookups['top/bot'][ss[14]]
		self.text        = ss[15]
