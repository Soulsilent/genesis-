"""
genesis所需要的数学类
"""
import math
import copy


def floatReserveDecimalPoint(floatPointNumber:float, digit:int=0) -> float:
	"""保留小数点位数"""

	string = '%%.%df' % digit
	return float(string % floatPointNumber)


def isFloatApproximate(number1:float, number2:float, precision:float=0.01):
	"""约等于"""

	if abs(number1 - number2) <= precision:
		return True
	else:
		return False


def floatTransformStringWithoutExtraZero(number:float=0):
	"""浮点数转字符串没有多余的0"""

	return str(number).strip('.0')


class Empty:
	"""空类"""

	def __init__(self):
		pass


class Point:
	"""点"""

	def __init__(self, x:float=0, y:float=0):
		self.x:float = x
		self.y:float = y
		self.tuple = None

	def __getattribute__(self, item):

		if item == 'tuple':
			self.__getTuple()

		return object.__getattribute__(self, item)

	def __getTuple(self):
		"""坐标的元组"""

		self.__dict__['tuple'] = (self.x, self.y)

	def copy(self):
		"""复制"""

		return copy.deepcopy(self)

	def set(self, x:float=0, y:float=0):
		"""设置数"""

		self.x = x
		self.y = y

	def move(self, x:float=0, y:float=0):
		"""改变数值"""

		self.x += x
		self.y += y

	def skewing(self, size:float, radian:float):
		"""偏移"""

		self.move(x=size * math.cos(radian), y=size * math.sin(radian))

	@staticmethod
	def getTwoPointDistance(point1, point2) -> float:
		"""两点间距"""

		return math.hypot(point2.x - point1.x, point2.y - point1.y)

	@staticmethod
	def isTwoPointEqual(point1, point2):
		"""两点相同"""

		return point1.tuple == point2.tuple


class Segment:
	"""线段"""

	def __init__(self, startPoint:Point=Point(), endPoint:Point=Point()):
		self.startPoint = startPoint
		self.endPoint = endPoint
		self.centerPoint = None
		self.length = None
		self.radian = None
		self.angle = None
		self.unitVector = None
		self.tuple = None
		self.limits = None

	def __getattribute__(self, item):

		if item == 'length':
			self.__getLength()
		elif item == 'radian':
			self.__getRadian()
		elif item == 'angle':
			self.__getAngle()
		elif item == 'unitVector':
			self.__getUnitVector()
		elif item == 'tuple':
			self.__getTuple()
		elif item == 'limits':
			self.__getLimits()
		elif item == 'centerPoint':
			self.__getCenterPoint()

		return object.__getattribute__(self, item)

	def __getLength(self):
		"""长度"""
		self.__dict__['length'] = math.hypot(self.endPoint.x - self.startPoint.x, self.endPoint.y - self.startPoint.y)

	def __getRadian(self):
		"""斜率弧度"""

		self.__dict__['radian'] = math.atan2(self.endPoint.y - self.startPoint.y, self.endPoint.x - self.startPoint.x)

	def __getAngle(self):
		"""斜率角度"""

		self.__dict__['angle'] = int('%.0f' % math.degrees(self.radian))

	def __getUnitVector(self):
		"""单位向量"""

		self.__dict__['unitVector'] = (math.cos(self.radian), math.sin(self.radian))

	def __getTuple(self):
		"""获得元组"""

		self.__dict__['tuple'] = (self.startPoint.tuple, self.endPoint.tuple)

	def __getLimits(self):
		"""获得尺寸范围"""

		limitsAssist = Empty()
		limitsAssist.xMin = min([self.startPoint.x, self.endPoint.x])
		limitsAssist.yMin = min([self.startPoint.y, self.endPoint.y])
		limitsAssist.xMax = max([self.startPoint.x, self.endPoint.x])
		limitsAssist.yMax = max([self.startPoint.y, self.endPoint.y])

		self.__dict__['limits'] = limitsAssist

	def __getCenterPoint(self):
		"""获取中点"""

		self.__dict__['centerPoint'] = Point(x=(self.startPoint.x + self.endPoint.x) / 2, y=(self.startPoint.y + self.endPoint.y) / 2)

	def invert(self):
		"""首尾翻转"""

		self.startPoint, self.endPoint = self.endPoint, self.startPoint

	def set(self, startPoint:Point=Point(), endPoint:Point=Point()):
		"""设置数值"""

		self.startPoint = startPoint
		self.endPoint = endPoint

	def change(self, startPointX:float=0, startPointY:float=0, endPointX:float=0, endPointY:float=0):
		"""数值改变"""

		self.startPoint.move(x=startPointX, y=startPointY)
		self.endPoint.move(x=endPointX, y=endPointY)

	def move(self, x:float=0, y:float=0):
		"""移动"""

		self.startPoint.move(x=x, y=y)
		self.endPoint.move(x=x, y=y)

	def changeSegmentLength(self, size:float, position:str='start'):
		"""
		改变线段的长度
		@param size: 改变的尺寸<float>
		@param position: 参考点<str>/start:起点，center:中点，end:末尾
		@return:
		"""

		if position == 'start':
			self.endPoint.set(x=self.endPoint.x + size * self.unitVector[0], y=self.endPoint.y + size * self.unitVector[1])
		elif position == 'end':
			self.startPoint.set(x=self.startPoint.x - size * self.unitVector[0], y=self.startPoint.y - size * self.unitVector[1])

	def copy(self):
		"""复制对象"""

		return copy.deepcopy(self)

	def skewing(self, size:float, direction:str='right'):
		"""偏移,方向左右"""

		if direction == 'right':
			self.move(x=size * math.cos(self.radian - math.pi / 2), y=size * math.sin(self.radian - math.pi / 2))
		elif direction == 'left':
			self.move(x=size * math.cos(self.radian + math.pi / 2), y=size * math.sin(self.radian + math.pi / 2))

	def rotate(self, radian:float, position:int=0):
		"""旋转,0:起点，1:中点，2:末尾"""

		if position == 0:
			self.endPoint.set(x=self.startPoint.x + self.length * math.cos(self.radian + radian), y=self.startPoint.y + self.length * math.sin(self.radian + radian))
		elif position == 2:
			self.startPoint.set(x=self.endPoint.x + self.length * math.cos(self.radian + math.pi + radian), y=self.endPoint.y + self.length * math.sin(self.radian + math.pi + radian))

	@staticmethod
	def getSegmentNearest(segment1, segment2):
		"""链接两个线段最接近的两点为一个新的线段"""

		distance1 = Point.getTwoPointDistance(point1=segment1.startPoint, point2=segment2.startPoint)
		distance2 = Point.getTwoPointDistance(point1=segment1.startPoint, point2=segment2.endPoint)
		distance3 = Point.getTwoPointDistance(point1=segment1.endPoint, point2=segment2.startPoint)
		distance4 = Point.getTwoPointDistance(point1=segment1.endPoint, point2=segment2.endPoint)

		minDistance = min([distance1, distance2, distance3, distance4])

		if distance1 == minDistance:
			return Segment(startPoint=segment1.startPoint.copy(), endPoint=segment2.startPoint.copy())
		elif distance2 == minDistance:
			return Segment(startPoint=segment1.startPoint.copy(), endPoint=segment2.endPoint.copy())
		elif distance3 == minDistance:
			return Segment(startPoint=segment1.endPoint.copy(), endPoint=segment2.startPoint.copy())
		elif distance4 == minDistance:
			return Segment(startPoint=segment1.endPoint.copy(), endPoint=segment2.endPoint.copy())

	@staticmethod
	def isTwoSegmentEquality(segment1, segment2):
		"""判断两个线段是否一致"""

		if (Point.isTwoPointEqual(point1=segment1.startPoint, point2=segment2.startPoint) and Point.isTwoPointEqual(point1=segment1.endPoint, point2=segment2.endPoint)) or (Point.isTwoPointEqual(point1=segment1.startPoint, point2=segment2.endPoint) and Point.isTwoPointEqual(point1=segment1.endPoint, point2=segment2.startPoint)):
			return True
		else:
			return False

	@staticmethod
	def getTwoSegmentAngle(segment1, segment2) -> float:
		"""获得两线段夹角，锐角，单位弧度"""

		return math.acos(segment1.unitVector[0] * segment2.unitVector[0] + segment1.unitVector[1] * segment2.unitVector[1])

	@staticmethod
	def getTwoSegmentAngleBisectorUnitVector(segment1, segment2):
		"""获得两线段夹角平分线的单位向量"""

		radian = math.atan2(segment1.unitVector[1] + segment2.unitVector[1], segment1.unitVector[0] + segment2.unitVector[0])

		return (math.cos(radian), math.sin(radian))

	@staticmethod
	def isPointSegmentCollinear(point:Point, segment):
		"""判断点与线段共线"""

		vector1 = (segment.startPoint.x - point.x, segment.startPoint.y - point.y)
		vector2 = (segment.endPoint.x - point.x, segment.endPoint.y - point.y)
		if vector1[0] * vector2[1] - vector2[0] * vector1[1] == 0:
			return True
		else:
			return False

	@staticmethod
	def isTwoSegmentCollinear(segment1, segment2):
		"""判断两线段是否共线"""

		if Segment.isPointSegmentCollinear(point=segment1.startPoint, segment=segment2) and Segment.isPointSegmentCollinear(point=segment1.endPoint, segment=segment2):
			return True
		else:
			return False

	@staticmethod
	def isPointOnSegment(point:Point, segment, includeEndPoint:bool=True):
		"""判断点是否在线段内"""

		if includeEndPoint:
			vector1 = (segment.startPoint.x - point.x, segment.startPoint.y - point.y)
			vector2 = (segment.endPoint.x - point.x, segment.endPoint.y - point.y)
			if vector1[0] * vector2[1] - vector2[0] * vector1[1] == 0 and vector1[0] * vector2[0] + vector1[1] * vector2[1] <= 0:
				return True
			else:
				return False
		else:
			vector1 = (segment.startPoint.x - point.x, segment.startPoint.y - point.y)
			vector2 = (segment.endPoint.x - point.x, segment.endPoint.y - point.y)
			if vector1[0] * vector2[1] - vector2[0] * vector1[1] == 0 and vector1[0] * vector2[0] + vector1[1] * vector2[1] < 0:
				return True
			else:
				return False

	@staticmethod
	def isSegmentOnSegment(segment, referSegment):
		"""判断线段是否在另一个线段内"""

		if Segment.isPointOnSegment(point=segment.startPoint, segment=referSegment) and Segment.isPointOnSegment(point=segment.endPoint, segment=referSegment):
			return True
		else:
			return False

	@staticmethod
	def isSegmentIncludeSegments(segment, segments:list):
		"""判断一条线段是否包含一组线段的至少一个"""

		for item in segments:
			if Segment.isSegmentOnSegment(segment=item, referSegment=segment):
				return True

		return False

	@staticmethod
	def getPointToSegmentDistanceForVertical(point, segment):
		"""点到直线的垂直距离, 正的为右侧，负的为左侧"""

		vector1 = (point.x - segment.startPoint.x, point.y - segment.startPoint.y)
		vector2 = (segment.endPoint.x - segment.startPoint.x, segment.endPoint.y - segment.startPoint.y)

		return (vector1[0] * vector2[1] - vector2[0] * vector1[1]) / segment.length


class Camber:
	"""弧形"""

	def __init__(self, startPoint:Point=Point(), endPoint:Point=Point(), centerPoint:Point=Point(), direction:str='CW'):
		"""CW：顺时针，CCW：逆时针"""
		self.startPoint = startPoint
		self.endPoint = endPoint
		self.centerPoint = centerPoint
		self.direction = direction
		self.radius = None
		self.radian = None
		self.angle = None
		self.tuple = None
		self.limits = None
		self.radianTotal = None
		self.length = None

	def __getattribute__(self, item):

		if item == 'radius':
			self.__getRadius()
		elif item == 'radian':
			self.__getRadian()
		elif item == 'angle':
			self.__getAngle()
		elif item == 'tuple':
			self.__getTuple()
		elif item == 'limits':
			self.__getLimits()
		elif item == 'radianTotal':
			self.__getRadianTotal()
		elif item == 'length':
			self.__getLength()

		return object.__getattribute__(self, item)

	def __getRadius(self):
		"""圆弧半径"""

		self.__dict__['radius'] = Point.getTwoPointDistance(point1=self.startPoint, point2=self.centerPoint)

	def __getRadian(self):
		"""弧度范围，总计(-pi, pi]"""

		if self.direction == 'CW':
			radianAssist = (Segment(startPoint=self.centerPoint, endPoint=self.endPoint).radian, Segment(startPoint=self.centerPoint, endPoint=self.startPoint).radian)
			if radianAssist[0] < radianAssist[1]:
				self.__dict__['radian'] = (radianAssist[0], radianAssist[1])
			else:
				self.__dict__['radian'] = ((-math.pi, radianAssist[1]), (radianAssist[0], math.pi))
		elif self.direction == 'CCW':
			radianAssist = (Segment(startPoint=self.centerPoint, endPoint=self.startPoint).radian, Segment(startPoint=self.centerPoint, endPoint=self.endPoint).radian)
			if radianAssist[0] < radianAssist[1]:
				self.__dict__['radian'] = (radianAssist[0], radianAssist[1])
			else:
				self.__dict__['radian'] = ((-math.pi, radianAssist[1]), (radianAssist[0], math.pi))

	def __getAngle(self):
		"""角度范围，总计(-180, 180]"""

		if self.direction == 'CW':
			radianAssist = (Segment(startPoint=self.centerPoint, endPoint=self.endPoint).angle, Segment(startPoint=self.centerPoint, endPoint=self.startPoint).angle)
			if radianAssist[0] < radianAssist[1]:
				self.__dict__['angle'] = (radianAssist[0], radianAssist[1])
			else:
				self.__dict__['angle'] = ((-180, radianAssist[1]), (radianAssist[0], 180))
		elif self.direction == 'CCW':
			radianAssist = (Segment(startPoint=self.centerPoint, endPoint=self.startPoint).angle, Segment(startPoint=self.centerPoint, endPoint=self.endPoint).angle)
			if radianAssist[0] < radianAssist[1]:
				self.__dict__['angle'] = (radianAssist[0], radianAssist[1])
			else:
				self.__dict__['angle'] = ((-180, radianAssist[1]), (radianAssist[0], 180))

	def __getTuple(self):
		"""获得元组"""

		self.__dict__['tuple'] = (self.startPoint.tuple, self.endPoint.tuple, self.centerPoint.tuple, self.direction)

	def __getLimits(self):
		"""获得范围"""

		limitsAssist = Empty()
		limitsX = [self.startPoint.x, self.endPoint.x]
		limitsY = [self.startPoint.y, self.endPoint.y]
		if type(self.radian[0]) is float:
			if self.radian[0] <= -math.pi <= self.radian[1]:
				limitsX.append(self.centerPoint.x - self.radius)
			if self.radian[0] <= -math.pi / 2 <= self.radian[1]:
				limitsY.append(self.centerPoint.y - self.radius)
			if self.radian[0] <= 0 <= self.radian[1]:
				limitsX.append(self.centerPoint.x + self.radius)
			if self.radian[0] <= math.pi / 2 <= self.radian[1]:
				limitsY.append(self.centerPoint.y + self.radius)
			if self.radian[0] <= math.pi <= self.radian[1]:
				limitsX.append(self.centerPoint.x - self.radius)
		else:
			if self.radian[0][0] <= -math.pi <= self.radian[0][1] or self.radian[1][0] <= -math.pi <= self.radian[1][1]:
				limitsX.append(self.centerPoint.x - self.radius)
			if self.radian[0][0] <= -math.pi / 2 <= self.radian[0][1] or self.radian[1][0] <= -math.pi / 2 <= self.radian[1][1]:
				limitsY.append(self.centerPoint.y - self.radius)
			if self.radian[0][0] <= 0 <= self.radian[0][1] or self.radian[1][0] <= 0 <= self.radian[1][1]:
				limitsX.append(self.centerPoint.x + self.radius)
			if self.radian[0][0] <= math.pi / 2 <= self.radian[0][1] or self.radian[1][0] <= math.pi / 2 <= self.radian[1][1]:
				limitsY.append(self.centerPoint.y + self.radius)
			if self.radian[0][0] <= math.pi <= self.radian[0][1] or self.radian[1][0] <= math.pi <= self.radian[1][1]:
				limitsX.append(self.centerPoint.x - self.radius)
		limitsAssist.xMin = min(limitsX)
		limitsAssist.yMin = min(limitsY)
		limitsAssist.xMax = max(limitsX)
		limitsAssist.yMax = max(limitsY)

		self.__dict__['limits'] = limitsAssist

	def __getRadianTotal(self):
		"""弧度总和"""

		# 获取总弧度
		if type(self.radian[0]) is float:
			self.__dict__['radianTotal'] = self.radian[1] - self.radian[0]
		else:
			self.__dict__['radianTotal'] = self.radian[0][1] - self.radian[0][0] + self.radian[1][1] - self.radian[1][0]

	def __getLength(self):
		"""弧长"""

		self.__dict__['length'] = self.radianTotal * self.radius

	def copy(self):
		"""复制"""

		return copy.deepcopy(self)

	def invert(self):
		"""首尾翻转"""

		assistDict = {'CW':'CCW', 'CCW':'CW'}
		self.startPoint, self.endPoint = self.endPoint, self.startPoint
		self.direction = assistDict[self.direction]

	def set(self, startPoint:Point=Point(), endPoint:Point=Point(), centerPoint:Point=Point(), direction:str='CW'):
		"""设置值"""

		self.startPoint = startPoint
		self.endPoint = endPoint
		self.centerPoint = centerPoint
		self.direction = direction

	def changeRadius(self, size:float=0):
		"""改变半径"""

		# 起点终点线段
		startSegment = Segment(startPoint=self.centerPoint.copy(), endPoint=self.startPoint.copy())
		endSegment = Segment(startPoint=self.centerPoint.copy(), endPoint=self.endPoint.copy())

		# 改变
		startSegment.changeSegmentLength(size=size, position=0)
		endSegment.changeSegmentLength(size=size, position=0)
		self.startPoint = startSegment.endPoint.copy()
		self.endPoint = endSegment.endPoint.copy()

	def move(self, x:float=0, y:float=0):
		"""移动"""

		self.startPoint.move(x=x, y=y)
		self.endPoint.move(x=x, y=y)
		self.centerPoint.move(x=x, y=y)

	def getChordLength(self, distance:float):
		"""获得距离圆心distance的弦长"""

		if 0 <= distance <= self.radius:
			return math.sqrt(self.radius ** 2 - distance**2) * 2
		else:
			return None

	def isRoundness(self):
		"""判断是否为圆圈"""

		if Point.isTwoPointEqual(point1=self.startPoint, point2=self.endPoint):
			return True
		else:
			return False
