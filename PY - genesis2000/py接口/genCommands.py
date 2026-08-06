#!/bin/env python
from genesisGeometry import *
import os


class TopCommands:

	def createJob(self, name, db_name):
		"""创建job"""

		for eachjob in self.jobs:
			if name == eachjob:
				return None
		self.COM('create_entity,job=,is_fw=no,type=job,name=' + name + ',db=' + db_name + ',fw_type=form')
		if self.STATUS:
			print("Some error in creating job " + name + " in db " + db_name)
		job = Job(name)
		job.close(1)

		return job

	def deleteJob(self, name):
		"""删除job"""

		joblist = self.listJobs()
		for eachjob in joblist:
			# If the job sxists, delete
			if name == eachjob:
				self.COM('delete_entity,job=,type=job,name=' + name)
				return self.STATUS

		return -1

	def importJob(self, fileAddress:str, jobName:str):
		"""导入job"""

		if jobName in self.jobs:
			return False
		else:
			self.COM(f'import_job,db=genesis,path={fileAddress:s},name={jobName:s},analyze_surfaces=no,verify_tgz=yes')
			return True

	def isCurrentStep(self, stepName:str):
		"""判断是否为当前step"""

		if stepName == self.currentStep:
			return True
		else:
			return False

	def openJobs(self):
		""" Returns a list of open jobs, as a list of strings"""
		jobList = self.DO_INFO('-t root')['gJOBS_LIST']
		openJobList = []
		for job in jobList:
			self.COM('is_job_open,job=%s' % job)
			if self.COMANS == 'yes':
				openJobList.append(job)
		return openJobList

	def getUser(self):
		""" Returns the name, as a string, of the current user"""

		self.COM('get_user_name')
		self.user = self.COMANS

		return self.user


class JobCommands:

	def open(self, lock):
		"""Open the job, and checkout if so indicated lock - integer: if > 1, job is checked out/locked"""
		self.COM('is_job_open,job=%s' % self.name)
		if self.COMANS == 'yes':
			if (lock > 0):
				self.COM('check_inout,mode=out,type=job,job=' + self.name)
			else:
				self.COM('check_inout,mode=test,type=job,job=' + self.name)
				if not (self.COMANS == 'no'):
					self.COM('check_inout,mode=in,type=job,job=' + self.name)
		else:
			STR = 'open_job,job=%s' % (self.name)
			self.COM(STR)
			self.group = self.COMANS
			if ((self.STATUS < 1) and (lock > 0) ):
				self.COM('check_inout,mode=out,type=job,job=' + self.name)    
		return self.STATUS

	def close(self, unlock):
		""" Close job represented by this class.unlock - if > 1, checks in/unlocks the job"""
		self.COM('close_job,job=' + self.name)
		if ((self.STATUS < 1) and (unlock > 0)):
			self.COM('check_inout,mode=test,type=job,job=' + self.name)
			if not (self.COMANS == 'no'):
				self.COM('check_inout,mode=in,type=job,job=' + self.name)
		return self.STATUS

	def addStep(self, name):
		"""添加step"""

		self.COM('create_entity,job=%s,is_fw=no,type=step,name=%s,fw_type=form' % (self.name,name))
		self.group = self.COMANS

		return self.STATUS

	def removeStep(self, name):

		self.COM('delete_entity,job=%s,type=step,name=%s' % (self.name,name))
		self.group = self.COMANS

		return self.STATUS
		
	def setGenesisAttr(self, name, value):
		"""设置属性"""

		self.COM('set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=%s,value=%s,units=inch' % (self.name,name,str(value)))
		setattr(self, name, value)
		
		return self.STATUS

	def importForm(self, formName, newFormName=''):
		"""导入form"""

		if newFormName == '':
			STR = 'copy_form,src_job=genesislib,src_form=%s,dst_job=%s,dst_form=%s' % (formName, self.name, formName)
		else:
			STR = 'copy_form,src_job=genesislib,src_form=%s,dst_job=%s,dst_form=%s' % (formName, self.name, newFormName)
		self.COM(STR)

		return self.STATUS

	def saveJob(self):
		"""保存料号"""

		if self.isChanged:
			self.COM('save_job,job=%s,override=no' % self.name)

	
class StepCommands:
	"""step对象的方法"""

	def open(self, iconic='no', zoomHone:bool=True):
		"""step的编辑窗口被打开，并设置组，并且step的group属性只有这里能改变"""

		self.COM('open_entity,job=%s,type=step,name=%s,iconic=%s' % (self.job.name, self.name, iconic))
		self.group = self.COMANS
		self.stepInitialize(zoomHome=zoomHone)

	def close(self):
		"""关闭窗口"""

		self.COM('editor_page_close')

	def zoomHome(self):
		"""视图归中"""

		self.COM('zoom_home')

	def zoomArea(self, point1:Point, point2:Point):
		"""切换视图"""

		self.COM(f'zoom_area,x1={str(point1.x):s},y1={str(point1.y):s},x2={str(point2.x):s},y2={str(point2.y):s}')

	def displaySR(self, yesOrNo:str='yes'):
		"""显示虚影"""

		self.COM('display_sr,display=%s' % yesOrNo)

	def displayNegative(self, mode:str='dim'):
		"""
		显示负性
		@param mode: 模式<str>/dim:暗淡，clear:清除
		@return:
		"""

		self.COM(f'negative_data,mode={mode:s}')

	def createProfile(self, point1:Point=None, point2:Point=None):
		"""创建轮廓"""

		if point1 and point2:
			self.COM(f'profile_rect,x1={str(point1.x):s},y1={str(point1.y):s},x2={str(point2.x):s},y2={str(point2.y):s}')
		else:
			self.COM('sel_create_profile')

	def displayProfile(self, yesOrNo:str='yes'):
		"""显示profile或者no"""

		self.COM('display_profile,display=%s' % yesOrNo)
		
	def setGenesisAttr(self, name, value):
		"""属性"""

		STR = 'set_attribute,type=step,job=%s,name1=%s,name2=,name3=,attribute=%s,value=%s,units=inch' % (self.job.name,self.name,name,str(value))
		self.COM(STR)
		setattr(self, name, value)

		return self.STATUS

	def changeUnit(self, unit:str):
		"""改变单位"""

		self.COM(f'units,type={unit:s}')

	def getMouseCoordinate(self, mode:str='p', msg:str=''):
		"""
		获取鼠标坐标
		@param mode: 模式<str>/p:一点/r:两点
		@param msg: 提示信息
		@return: 单点：点/双点：线段
		"""

		if mode == 'p':
			self.MOUSE(mode=mode, msg=msg)
			stringList = self.MOUSEANS.split()
			return Point(x=float(stringList[0]), y=float(stringList[1]))
		elif mode == 'r':
			self.MOUSE(mode=mode, msg=msg)
			stringList = self.MOUSEANS.split()
			return Segment(startPoint=Point(x=float(stringList[0]), y=float(stringList[1])), endPoint=Point(x=float(stringList[2]), y=float(stringList[3])))

	def layersBackups(self, layers:str, prefix:str= '', suffix:str= '_backup', mode:str= 'replace'):
		"""
		层备份
		@param layers: 要备份层名<str>/用|分割多个
		@param prefix: 前缀<str>
		@param suffix: 后缀<str>
		@param mode: 模式<str>/replace:替换
		@return:
		"""

		if mode == 'replace':
			for layer in layers.split('|'):
				if self.isLayersExist(layers=f'{prefix:s}{layer:s}{suffix:s}'):
					self.copyLayerFeatures(sourceJob=self.job.name, sourceStep=self.name, sourceLayer=f'{prefix:s}{layer:s}{suffix:s}', destLayer=layer)
				else:
					self.copyLayerFeatures(sourceJob=self.job.name, sourceStep=self.name, sourceLayer=layer, destLayer=f'{prefix:s}{layer:s}{suffix:s}')
		elif mode == 'saveAbsolutely':
			for layer in layers.split('|'):
				self.copyLayerFeatures(sourceJob=self.job.name, sourceStep=self.name, sourceLayer=layer, destLayer=f'{prefix:s}{layer:s}{suffix:s}')


	"""
	层相关操作
	"""
	def reLayerName(self, name: str, newName: str):
		"""更改层名"""

		self.COM('rename_layer,name=%s,new_name=%s' % (name, newName))

	def isWorkLayer(self, layerName:str) -> bool:
		"""判断层是否为工作层"""

		if layerName == self.workLayer:
			return True
		else:
			return False

	def setWorkLayer(self, layerName:str):
		"""设置工作层"""

		self.displayLayer(layerName=layerName, number=1, work=True)
	
	def displayLayer(self, layerName:str, number:int,  display:str='yes', work:bool=False):
		"""显示层"""

		self.COM('display_layer,name=%s,display=%s,number=%s' % (layerName, display, str(number)))
		if work:
			self.COM('work_layer,name=%s' % layerName)

	def clearAll(self):
		"""清除影响层，显示层和高亮"""

		self.COM('clear_layers')
		self.COM('clear_highlight')
		self.affectAllLayers(affected='no')

	def stepInitialize(self, zoomHome:bool=True):
		"""step初始化"""

		self.clearAll()
		self.setFilter()
		self.changeUnit(unit=self.unit)
		self.currentAttributeSet()
		if zoomHome:
			self.zoomHome()

	def affectAllLayers(self, affected:str='yes'):
		"""影响所有层"""

		self.COM('affected_layer,mode=all,affected=%s' % affected)

	def affectLayers(self, layers:str, affected:str='yes'):
		"""影响多层,用|隔开"""

		for layer in self.isLayersExist(layers=layers, logic='or'):
			self.COM('affected_layer,name=%s,mode=single,affected=%s' % (layer, affected))

	def createLayer(self, layerName:str, context:str='misc', layerType:str='document', polarity:str='positive', insLayer:str='', replace:bool=True):
		"""创建层"""

		if replace:
			self.removeLayers(layers=layerName)
		self.COM('create_layer,layer=%s,context=%s,type=%s,polarity=%s,ins_layer=%s' % (layerName, context, layerType, polarity, insLayer))

	def removeLayers(self, layers:str):
		"""移除层"""

		layersList = layers.split('|')

		for layer in layersList:
			if layer in self.layers:
				self.COM('delete_layer,layer=%s' % layer)

	def removeLayersByString(self, string: str):
		"""删除层通过字符串"""

		self.removeLayers(layers='|'.join(self.isLayersExistByString(string=string)))

	def isLayersExist(self, layers:str, logic:str='and'):
		"""判断层是否存在,用|分开"""

		layersList = layers.split('|')
		if logic == 'and':
			if set(layersList).issubset(set(self.layers)):
				return True
			else:
				return False
		if logic == 'or':
				layerAssist = []
				for layer in layersList:
					if layer in self.layers:
						layerAssist.append(layer)
				return layerAssist

	def isLayersExistByString(self, string:str):
		"""通过层名判断是否存在指定层"""

		layersList = []
		for layer in self.layers:
			if string in layer:
				layersList.append(layer)

		return layersList

	def mergeLayers(self, sourceLayer:str, destLayer:str, invert:str='no'):
		"""合并层"""

		self.COM('merge_layers,source_layer=%s,dest_layer=%s,invert=%s' % (sourceLayer, destLayer, invert))

		return self.STATUS

	"""
	属性设置
	"""
	def currentAttributeSet(self, attributes:str= ''):
		"""设置当前属性, 用|分割"""

		self.COM('cur_atr_reset')
		if attributes:
			attributes = attributes.split('|')
			if len(attributes) == 1:
				self.COM('cur_atr_set,attribute=%s' % attributes[0])
			else:
				self.COM('cur_atr_set,attribute=%s,text=%s,option=%s' % (attributes[0], attributes[1], attributes[1]))

	def defineFeaturesAttribute(self, attributes:str= ''):
		"""定义features属性"""

		self.currentAttributeSet(attributes=attributes)
		self.COM('sel_change_atr,mode=add')
		self.currentAttributeSet()

	def deleteAllAttributes(self):
		"""删除所有Attributes"""

		self.COM('sel_delete_atr,attributes=.area\;.dummy_pin\;.avoid_pattern_fill\;.avoid_shave\;.clear_dont_opt\;.tapering_feature\;.detch_comp\;.detch_smooth\;.detch_tapering\;.force_galv_etch\;.osp_pad\;.bonding_pad_comp\;.brk_point\;.canned_text\;.critical_net\;.critical_tp\;.deferred\;.dont_repair\;.drill_noopt\;.dxf_dimension\;.et_align\;.et_stamp\;.etch_comp_addition\;.foot_down\;.full_plane\;.gold_plating\;.hatch\;.hatch_border\;.ignore_action\;.imp_line\;.is_capped\;.lpol_surf\;.mount_hole\;.n_electric\;.net_point\;.nfp\;.nfl\;.nomenclature\;.non_tp\;.non_np\;.notest_req\;.orbotech_plot_stamp\;.out_nc_ignore\;.out_nc_verif\;.out_orig\;.patch\;.pattern_fill\;.plating_bar\;.rout_plated\;.shave\;.sliver_fill\;.smd\;.bga\;.via_pad\;.laser_via_pad\;.pth_pad\;.npth_pad\;.copper_defined\;.solder_defined\;.embedded\;.partially_embedded\;.covered\;.partially_covered\;.smooth\;.tear_drop\;.test_point\;.test_req\;.tie\;.tie_plane\;.tiedown\;.tooling_hole\;.drawing_outline\;.drawing_template\;.drawing_profile\;.orig_tooling_holes_set\;.out_break\;.out_scale\;.out_drill_optional\;.out_rout_optional\;.critical_trace\;.non_critical_trace\;.non_functional_trace\;.hatch_serrated_border\;.string_mirrored\;.bump_pad\;.ball_pad\;.area_name\;.bit\;.cdr14_zone_type\;.cdr14_stages\;.color\;.etm_pin_name\;.fiducial_name\;.geometry\;.inp_net_name\;.orig_features\;.dfm_added_shave\;.orig_size_mm\;.orig_size_inch\;.source_llayer\;.step_numbering\;.imp_info\;.string\;.rout_message\;.tooling_holes_purpose\;.pnl_place\;.spo_shape\;.hp3070_probe_access\;.net_name\;.net_physical_type\;.net_spacing_type\;.detch_orig_type\;.comp\;.drill\;.drill_sr_zero\;.drill_stage\;.drill_first_last\;.etm_constant_drill_usage\;.generated_net_point\;.orbotech_barcode_string\;.pad_usage\;.plated_type\;.rout_plunge_mode\;.rout_pocket_direction\;.rout_snake_direction\;.rout_pocket_mode\;.rout_type\;.via_type_pad\;.via_type\;.pressure_foot\;.spo_w_mode\;.spo_h_mode\;.spo_s_mode\;.spo_p_mode\;.test_potential\;.sip\;.aoi_cpbm\;.aoi_cpcu\;.aoi_drbm\;.aoi_drcu\;.aoi_value\;.detch_orig_nf\;.cdr_val\;.connection_id\;.cut_line\;.drill_flag\;.extended\;.feed\;.imp_line_candidate\;.jtag_component_id\;.orig_surf\;.out_flag\;.pilot_hole\;.rout_chain\;.rout_cutoff_feed\;.rout_flag\;.rout_plunge_feed\;.rout_plunge_val_v1\;.rout_plunge_val_v2\;.rout_pocket_feed\;.side_proximity\;.speed\;.infeed_speed\;.retract_speed\;.tooling_holes_set\;.tooling_holes_relation\;.tooling_holes_index\;.lyr_prf_ref\;.feature_fill_margin\;.combined_size\;.pilot_hole_offset_along\;.pilot_hole_offset_perpend\;.pitch\;.rout_plunge_val_a\;.rout_plunge_val_b\;.rout_plunge_val_c\;.rout_plunge_val_d\;.rout_plunge_val_e\;.rout_plunge_val_f\;.rout_pocket_overlap\;.rout_grid_x_offset\;.rout_grid_y_offset\;.rout_tool\;.rout_tool2\;.spacing_req\;.surface_outline_widths\;.drawing_magnify\;.depth\;.spo_move_center\;.spo_w_val\;.spo_w_fact\;.spo_h_val\;.spo_h_fact\;.spo_s_val\;.spo_s_fact\;.string_angle')

	"""
	参选器设置
	"""
	def setFilter(self, featuresTypes:str='', polarity:str='', symbols:str='', attributes:str=''):
		"""设置参选器参数"""

		self.COM('filter_reset,filter_name=popup')
		if featuresTypes:
			featuresTypes = featuresTypes.replace('|','\;')
			self.COM('filter_set,filter_name=popup,update_popup=yes,feat_types=%s' % featuresTypes)
		if polarity:
			polarity = polarity.replace('|','\;')
			self.COM('filter_set,filter_name=popup,update_popup=yes,polarity=%s' % polarity)
		if symbols:
			symbols = symbols.replace('|','\;')
			self.COM('filter_set,filter_name=popup,update_popup=yes,include_syms=%s' % symbols)
		if attributes:
			attributes = attributes.split('|')
			if len(attributes) == 1:
				self.COM('filter_atr_set,filter_name=popup,condition=no,attribute=%s' % attributes[0])
			else:
				self.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=%s,text=%s,option=%s' % (attributes[0], attributes[1], attributes[1]))

	"""
	选择物件
	"""
	def selectSingleFeature(self, point:Point=Point(x=0, y=0)):
		"""选择单一物件"""

		self.COM(f'sel_single_feat,operation=select,x={str(point.x):s},y={str(point.y):s}')

	def selectNoneFeature(self):
		"""取消所有选择"""

		self.COM('sel_clear_feat')

	def selectAllFeatures(self):
		"""选择所有物件"""

		self.COM('filter_area_strt')
		self.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0')

	def reverseSelectedFeatures(self):
		"""反选"""

		self.COM('sel_reverse')

	def selectFeaturesByReference(self, layerName: str, mode: str='cover', featuresTypes:str='line|pad|surface|arc|text', polarity:str='positive|negative', attributes:str='', logic:str='and'):
		"""参考选择"""

		featuresTypes = featuresTypes.replace('|', '\;')
		polarity = polarity.replace('|', '\;')
		self.COM('filter_atr_reset,filter_name=ref_select')
		if attributes:
			attributes = attributes.split('|')
			self.COM(f'filter_atr_logic,filter_name=ref_select,logic={logic:s}')
			if len(attributes) == 1:
				self.COM(f'filter_atr_set,filter_name=ref_select,condition=no,attribute={attributes[0]:s}')
			else:
				self.COM(f'filter_atr_set,filter_name=ref_select,condition=yes,attribute={attributes[0]:s},text={attributes[1]:s},option={attributes[1]:s}')
		self.COM('sel_ref_feat,layers=%s,use=filter,mode=%s,pads_as=shape,f_types=%s,polarity=%s,include_syms=,exclude_syms=,on_multiple=all' % (layerName, mode, featuresTypes, polarity))
		self.COM('filter_atr_reset,filter_name=ref_select')

	def selectFeaturesByIndex(self, layerName:str, index:int):
		"""
		选择指定序号的物件
		:param layerName: 层名
		:param index: 序号
		"""
		self.COM(f'sel_layer_feat,operation=select,layer={layerName:s},index={str(index):s}')
	
	def selectFeaturesByRectangle(self, xs, ys, xe, ye, intersect='no'):
		"""矩形区域选择"""

		self.COM('filter_area_strt')
		self.COM('filter_area_xy,x='+str(xs)+',y='+str(ys))
		self.COM('filter_area_xy,x='+str(xe)+',y='+str(ye))
		self.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area='+intersect)

		return str(self.COMANS)

	def selectViaPad(self):
		"""选择via pad"""
		self.selectNoneFeature()
		self.setFilter(featuresTypes='pad', polarity='positive', attributes='.drill|via')
		self.selectAllFeatures()
		self.setFilter()

	def selectNptPad(self):
		"""选择npt pad"""
		self.selectNoneFeature()
		self.setFilter(featuresTypes='pad|line', polarity='positive', attributes='.drill|non_plated')
		self.selectAllFeatures()
		self.setFilter()

	def selectPthPad(self):
		"""选择pth pad"""
		self.selectNoneFeature()
		self.setFilter(featuresTypes='pad|line', polarity='positive', attributes='.drill|plated')
		self.selectAllFeatures()
		self.setFilter()

	def selectSmdPad(self):
		"""选择smd"""
		self.selectNoneFeature()
		self.setFilter(featuresTypes='pad', polarity='positive', attributes='.smd')
		self.selectAllFeatures()
		self.setFilter()

	"""
	复制与移动
	"""
	def moveSelectedFeaturesToOtherLayer(self, targetLayer:str, invert:str='no', reSize:float=0, replace:bool=False):
		"""移动到另一层"""

		if replace:
			self.removeLayers(layers=targetLayer)
		self.COM(f'sel_move_other,target_layer={targetLayer:s},invert={invert:s},dx=0,dy=0,size={str(reSize):s},x_anchor=0,y_anchor=0,rotation=0,mirror=none')

	def moveSelected(self, x:float, y:float):
		"""同层移动选中"""

		self.COM('sel_move,dx=%s,dy=%s' % (str(x), str(y)))
		
	def deleteSelectedFeatures(self):
		"""删除选中物"""

		self.COM('sel_delete')

	def copySelectedFeaturesToOtherLayer(self, dest:str='layer_name', targetLayer:str='', invert:str='no', resize:float=0, replace:bool=False):
		"""
		复制选中的物件复制到另一层
		@param dest: 目标模式<str>/layer_name：层名模式，affected_layers:影响层
		@param targetLayer: 目标层<str>
		@param invert: 翻转极性<str>/yes,no
		@param resize: 改变尺寸<float>
		@param replace: 是否覆盖<bool>
		@return:
		"""

		if replace and targetLayer and dest == 'layer_name':
			self.removeLayers(layers=targetLayer)
		self.COM(f'sel_copy_other,dest={dest:s},target_layer={targetLayer:s},invert={invert:s},dx=0,dy=0,size={str(resize)},x_anchor=0,y_anchor=0,rotation=0,mirror=none')

	def copyLayerFeatures(self, sourceJob:str, sourceStep:str, sourceLayer:str, destLayer:str, mode:str='replace', invert:str='no'):
		"""跨step复制"""

		self.COM(f'copy_layer,source_job={sourceJob:s},source_step={sourceStep:s},source_layer={sourceLayer:s},dest=layer_name,dest_layer={destLayer:s},mode={mode:s},invert={invert:s},copy_notes=no,copy_attrs=new_layers_only,copy_sr_feat=no,copy_lpd=new_layers_only')

	"""
	checkList相关
	"""
	def createCheck(self, checkName):
		"""Create a new checklist checkName - name of new checklist"""
		STR = 'chklist_create,chklist=' + checkName
		self.COM(STR)
		self.getInfo()
		self.getChecks()
		return self.STATUS

	def deleteCheck(self, checkName):
		"""Delete a checklist checkName - name of checklist to delete"""
		STR = 'chklist_delete,chklist=' + checkName
		self.COM(STR)
		self.getInfo()
		self.getChecks()
		return self.STATUS

	def importCheck(self, checkName, replace = 0):
		"""get checklist from library - replace if indicated
		checkName - name of checklist to replace
		replace - defaults to 0, if > 0, existing checklist is replaced"""
		if replace:
			self.COM('chklist_create,chklist=' + checkName)
			self.COM('chklist_delete,chklist=' + checkName)
			self.COM('chklist_from_lib,chklist=' + checkName)
			self.getInfo()
			self.getChecks()
		else:
			self.VOF()
			self.COM('chklist_from_lib,chklist=' + checkName)
			self.VON()
			self.getInfo()
			self.getChecks()
		return self.STATUS

	"""
	缓冲器复制粘贴
	"""
	def buffCopy(self):
		"""Copy selected features to buffer"""
		self.COM('sel_buffer_copy,x_datum=0,ydatum=0')

	def buffPaste(self,x=0,y=0):
		"""Paste from buffer to x and y location indicated (defaults to origin)"""
		self.COM('sel_buffer_paste,x_datum='+str(x)+',y_datum='+str(y))
	
	def inputAuto(self, path, report_path = '', report_filename='', copy_to_job = 'no'):
		""" Run the input screen on a specific path.  Save the report to another specific path.
			path - path to look for input data
			report_path - path in which to save report data
			report_filename (optional)  will use jobname_inp.txt if not specified
			copy_to_job (optional) "yes" or "no" to tell if you want to copy input files to job input directory"""
		if report_path == '':
			report_path = path
		if report_filename == '':
			report_filename = self.job.name + '_inp.txt'	
		if not (report_path[len(report_path)-1] == '/'):
			report_full = report_path + '/' + report_filename
		else:
			report_full = report_path + report_filename
		STR = 'input_identify,path=%s,job=%s,script_path=%s,unify=yes,gbr_ext=yes,drl_ext=yes,gbr_units=auto,drl_units=auto,break_sr=no' % (path,self.job.name,report_full+'_id')
		self.COM(STR)
		STR = 'input_auto,path=%s,job=%s,step=%s,report_path=%s,copy_to_job=%s' % (path,self.job.name,self.name,report_full,copy_to_job)
		self.COM(STR)
		return self.STATUS
		
	"""FEATURE相关"""
	def addPad(self, geometry:Point, symbol:str, polarity:str = 'positive', angle:float = 0, mirror:str = 'no', nx:str = '1', ny:str = '1', dx:str = '0', dy:str = '0', xscale:str = '1', yscale:str = '1', attributes:str = 'no', attributeString:str= ''):
		"""添加pad"""

		if attributes == 'yes':
			self.currentAttributeSet(attributes=attributeString)
			self.COM('add_pad,attributes=%s,x=%s,y=%s,symbol=%s,polarity=%s,angle=%s,mirror=%s,nx=%s,ny=%s,dx=%s,dy=%s,xscale=%s,yscale=%s' % (attributes, str(geometry.x), str(geometry.y), symbol, polarity, str((360 - angle) % 360), mirror, nx, ny, dx, dy, xscale, yscale))
			self.currentAttributeSet()
		elif attributes == 'no':
			self.currentAttributeSet()
			self.COM('add_pad,attributes=%s,x=%s,y=%s,symbol=%s,polarity=%s,angle=%s,mirror=%s,nx=%s,ny=%s,dx=%s,dy=%s,xscale=%s,yscale=%s' % (attributes, str(geometry.x), str(geometry.y), symbol, polarity, str((360 - angle) % 360), mirror, nx, ny, dx, dy, xscale, yscale))

		return self.STATUS
		
	def addLine(self, geometry:Segment, symbol:str, polarity:str= 'positive', attributes:str= 'no', attributeString:str= ''):
		"""添加线"""
		if attributes == 'yes':
			self.currentAttributeSet(attributes=attributeString)
			self.COM('add_line,attributes=%s,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=%s' % (attributes, str(geometry.startPoint.x), str(geometry.startPoint.y), str(geometry.endPoint.x), str(geometry.endPoint.y), symbol, polarity))
			self.currentAttributeSet()
		elif attributes == 'no':
			self.currentAttributeSet()
			self.COM('add_line,attributes=%s,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=%s' % (attributes, str(geometry.startPoint.x), str(geometry.startPoint.y), str(geometry.endPoint.x), str(geometry.endPoint.y), symbol, polarity))

		return self.STATUS
		
	def addArc(self, geometry:Camber, symbol:str, polarity='positive', attributes='no'):
		"""arc"""
	
		self.COM('add_arc,attributes=%s,xs=%s,ys=%s,xe=%s,ye=%s,xc=%s,yc=%s,symbol=%s,polarity=%s,direction=%s' % (attributes, str(geometry.startPoint.x), str(geometry.startPoint.y), str(geometry.endPoint.x), str(geometry.endPoint.y), str(geometry.centerPoint.x), str(geometry.centerPoint.y), symbol, polarity, geometry.direction))
		
		return self.STATUS
		
	def addText(self, geometry:Point, text:str, xSize:float, ySize:float, fontName:str, width:float, attributes='no', txt_type:str='string', angle:float=0, mirror:str= 'no', polarity:str= 'positive'):
		"""添加字符"""

		if self.unit == 'mm':
			widthFactor = width / 304.8
		elif self.unit == 'inch':
			widthFactor = width * 25.4 / 304.8
		self.COM(
			'add_text,attributes=%s,type=%s,x=%s,y=%s,text=%s,x_size=%s,y_size=%s,w_factor=%s,polarity=%s,angle=%s,mirror=%s,fontname=%s,ver=1' % (
			attributes, txt_type, str(geometry.x), str(geometry.y), text, str(xSize / 1000), str(ySize / 1000),
			str(widthFactor), polarity, str((360 - angle) % 360), mirror, fontName))

	def changeText(self, text:str, xSize:float, ySize:float, fontName:str, width:float, angle:float=0, mirror:str= 'no', polarity:str= 'positive'):
		"""改变字符"""

		if self.unit == 'mm':
			widthFactor = width / 304.8
		elif self.unit == 'inch':
			widthFactor = width * 25.4 / 304.8
		self.COM(f'sel_change_txt,text={text:s},x_size={str(xSize / 1000):s},x_space=0,y_size={str(ySize / 1000):s},w_factor={str(widthFactor):s},polarity={polarity:s},angle={str((360 - angle) % 360):s},mirror={mirror:s},fontname={fontName:s}')

	def addChineseText(self, geometry: Point, text: str, xSize: float, ySize: float, fontName: str, width: float, attributes='no', angle: float = 0, mirror: str = 'no', polarity: str = 'positive'):
		"""添加中文字符"""

		if self.unit == 'mm':
			widthFactor = width / 304.8
		elif self.unit == 'inch':
			widthFactor = width * 25.4 / 304.8
		self.COM(f'add_text,mirror={mirror:s},bar_char_set=full_ascii,fontname={fontName:s},x={str(geometry.x):s},bar_type=UPC39,bar_height=0.178,y={str(geometry.y):s},text={text:s},bar_width=0.008,y_size={ySize / 1000:f},ver=1,x_size={xSize / 1000:f},angle={(360 - angle) % 360:f},bar_add_string_pos=top,bar_add_string=yes,w_factor={str(widthFactor)},bar_background=yes,polarity={polarity:s},type=string,attributes={attributes:s}')

	def addRectSurface(self, startPoint:Point, endPoint:Point, polarity:str='positive', attributes:str='no'):
		"""添加矩形的铜皮"""
	
		self.COM(f'add_surf_strt,surf_type=feature')
		self.COM(f'add_surf_poly_strt,x={str(startPoint.x):s},y={str(startPoint.y):s}')
		self.COM(f'add_surf_poly_seg,x={str(startPoint.x):s},y={str(endPoint.y):s}')
		self.COM(f'add_surf_poly_seg,x={str(endPoint.x):s},y={str(endPoint.y):s}')
		self.COM(f'add_surf_poly_seg,x={str(endPoint.x):s},y={str(startPoint.y):s}')
		self.COM(f'add_surf_poly_seg,x={str(startPoint.x):s},y={str(startPoint.y):s}')
		self.COM(f'add_surf_poly_end')
		self.COM(f'add_surf_end,attributes={attributes:s},polarity={polarity:s}')

	def addArrowLines(self, point:Point=Point(x=0, y=0), length:float=1500, width:float=150, angle:float=0, haveHeaderLine:bool=True):
		"""添加箭头"""

		# 初始选段
		pointAssist = point.copy()
		pointAssist.skewing(size=length / 1000, radian=math.radians(angle))
		origSegment = Segment(startPoint=point, endPoint=pointAssist)
		if haveHeaderLine:
			segment1 = origSegment.copy()
			segment1.rotate(position=0, radian=math.pi / 2)
			segment2 = origSegment.copy()
			segment2.rotate(position=0, radian=math.pi / 6)
			segment3 = origSegment.copy()
			segment3.rotate(position=0, radian=-math.pi / 2)
			segment4 = origSegment.copy()
			segment4.rotate(position=0, radian=-math.pi / 6)
			self.addLine(geometry=segment1, symbol=f'r{width:f}')
			self.addLine(geometry=segment2, symbol=f'r{width:f}')
			self.addLine(geometry=segment3, symbol=f'r{width:f}')
			self.addLine(geometry=segment4, symbol=f'r{width:f}')
			self.addLine(geometry=origSegment, symbol=f'r{width:f}')
		else:
			segment1 = origSegment.copy()
			segment1.rotate(position=0, radian=math.pi / 6)
			segment2 = origSegment.copy()
			segment2.rotate(position=0, radian=-math.pi / 6)
			self.addLine(geometry=segment1, symbol=f'r{width:f}')
			self.addLine(geometry=segment2, symbol=f'r{width:f}')
			self.addLine(geometry=origSegment, symbol=f'r{width:f}')
	
	def profileToRout(self, layerName:str, width:float):
		"""profile转外形"""

		self.COM(f'profile_to_rout,layer={layerName:s},width={str(width):s}')

	# ROUT EDITOR COMMANDS
	def addRoutChain(self, layer, size, compensation, feed, flag = 0, speed = 0, first = 0, change_direction = -1):
		""" Add selected features to a new rout chain.  This try rout chain 1, and if it fails,
		to try adding the chain, incrementing the chain number, until success.  It only goes to 100.
		Chain Number is returned.  If -1 returned, there was an error
			layer - layer to add rout chain to
			size (float) - size in inches for rout bit can be specified to 10th of mils only.
			compensation (str) - right, left, none
			feed (int) - feed rate
			flag (int) - default 0 - flag number
			speed (int) - default 0 - speed number
			first (int) - default 0 : -1 is not specified.  >0 is the first feature in chain. 0 is first of
					selected features to be added to layer (by index number), on up)
			change_direction (int) - defaults to -1 - not sure what it is for."""
		
		self.VOF()
		
		self.STATUS = 1
		chainNum = 0
		while (self.STATUS) and (chainNum <= 100):
			chainNum = chainNum + 1
			STR = 'chain_add,layer=%s,chain=%s,size=%.4f,comp=%s,flag=%s,feed=%s,speed=%s,first=%s,chng_direction=%s' % (layer, chainNum, size, compensation, flag, feed, speed, first, change_direction)
			self.COM(STR)
			print("Status: " + str(self.STATUS))
	
		self.VON()
		
		if (not self.STATUS):
			return chainNum
		else:
			return -1
			
	def setChainPlunge(self, layer, chain, len1, len2, intType = 'corner', mode = 'wrap', inl_mode = 'straight' , start_of_chain = 'yes', apply_to = 'all', len3 = 0.0, len4 = 0.0, val1 = 0, val2 = 0, ang1 = 0, ang2 = 0, ifeed = 0, ofeed = 0):
		""" Set up the plunge for a rout chain.  Lots and lots of options.  For now, you can look at 
		the code yourself."""
		
		self.COM('chain_list_reset')
		self.COM('chain_list_add,chain=' + str(chain))
		
		STR = 'chain_set_plunge,layer=%s,type=%s,mode=%s,inl_mode=%s,start_of_chain=%s,' % (layer, intType, mode, inl_mode, start_of_chain)
		STR = STR + 'apply_to=%s,len1=%.6f,len2=%.6f,len3=%.6f,len4=%.6f,val1=%s,val2=%s,ang1=%s,ang2=%s,ifeed=%s,ofeed=%s' % (apply_to,len1,len2,len3,len4,val1,val2,ang1,ang2,ifeed,ofeed)
		self.COM(STR)		
		return self.STATUS
		
	def routCopy(self, sourceLayer, destLayer, destType='document'):
		""" Copy a rout layer to another layer.  destType determines if copied as normal features or rout features
		Obliterates the layer you are copying to
			destType - 'document' or 'rout'   """			
		STR = 'compensate_layer,source_layer=%s,dest_layer=%s,dest_layer_type=%s' % (sourceLayer, destLayer, destType)
		self.COM(STR)		 
		return self.STATUS

	def chamfer(self, radius:int):
		"""倒角, 单位um"""

		self.COM(f'sel_intersect_best,function=find_connect,mode=round,radius={radius:d},length_x=0,length_y=0,type_x=length,type_y=length,show_all=no,keep_remainder1=no,keep_remainder2=no,ang_x=0,ang_y=0')

	def changeSymbol(self, symbol:str):
		"""改变symbol"""

		self.COM(f'sel_change_sym,symbol={symbol:s},reset_angle=no')

	def registerDrl(self):
		"""与drl对齐"""
		if self.unit == 'inch':
			self.COM('register_layers,reference_layer=drl,tolerance=1.5,mirror_allowed=yes,rotation_allowed=yes,zero_lines=no,reg_mode=affected_layers,register_layer=')
		if self.unit == 'mm':
			self.COM('register_layers,reference_layer=drl,tolerance=38.1,mirror_allowed=yes,rotation_allowed=yes,zero_lines=no,reg_mode=affected_layers,register_layer=')

	def selectedFeaturesContourize(self, mode:str='x_and_y', clearHole:float=3, accuracy:float=0.1):
		"""
		转成铜皮
		@param mode: area/x_and_y/x_or_y
		@param clearHole: 单位mil
		@return:
		"""

		if self.unit == 'inch':
			self.COM(f'sel_contourize,accuracy={str(accuracy):s},break_to_islands=yes,clean_hole_size={str(clearHole):s},clean_hole_mode={mode:s},validate_result=no')
		elif self.unit == 'mm':
			self.COM(f'sel_contourize,accuracy={str(accuracy * 25.4):s},break_to_islands=yes,clean_hole_size={str(clearHole * 25.4):s},clean_hole_mode={mode:s},validate_result=no')

	def designToRout(self):
		"""检测外形"""

		if self.unit == 'inch':
			self.COM('sel_design2rout,det_tol=1,con_tol=1,rad_tol=0.1')
		elif self.unit == 'mm':
			self.COM('sel_design2rout,det_tol=25.4,con_tol=25.4,rad_tol=2.54')

	def padToOutline(self):
		"""pad转外形"""

		self.COM('sel_pad2outline')

	def padToline(self):
		"""pad转线"""

		self.COM('sel_pad2line')

	def lineToPad(self):
		"""线转pad"""

		if self.unit == 'mm':
			self.COM('chklist_single,action=valor_cleanup_ref_subst,show=yes')
			self.COM('chklist_cupd,chklist=valor_cleanup_ref_subst,nact=1,params=((pp_layer=.affected)(pp_in_selected=All)(pp_tol=2.54)(pp_rot_mode=ALL)(pp_connected=Yes)(pp_work=Features)),mode=regular')
			self.COM('chklist_run,chklist=valor_cleanup_ref_subst,nact=1,area=profile')
			self.COM('chklist_close,chklist=valor_cleanup_ref_subst,mode=hide')

	def selectedFeaturesCutData(self):
		"""打散外形"""

		if self.unit == 'inch':
			self.COM('sel_cut_data,det_tol=1,con_tol=1,rad_tol=0.1,filter_overlaps=no,delete_doubles=no,use_order=yes,ignore_width=yes,ignore_holes=none,start_positive=yes,polarity_of_touching=same')
		if self.unit == 'mm':
			self.COM('sel_cut_data,det_tol=25.4,con_tol=25.4,rad_tol=2.54,filter_overlaps=no,delete_doubles=no,use_order=yes,ignore_width=yes,ignore_holes=none,start_positive=yes,polarity_of_touching=same')

	def surfaceToPad(self):
		"""铜皮转pad"""

		if self.unit == 'inch':
			self.COM('sel_cont2pad,match_tol=1,restriction=,min_size=5,max_size=100000,suffix=+++')
		elif self.unit == 'mm':
			self.COM('sel_cont2pad,match_tol=25.4,restriction=,min_size=127,max_size=2540000,suffix=+++')

	def surfaceToOutline(self, width:float):
		"""铜皮转外形"""

		self.COM(f'sel_surf2outline,width={str(width):s}')

	def selectLineBlock(self):
		"""选择线块"""

		self.COM('sel_drawn,type=mixed,therm_analyze=no')

	def deleteIsolateHole(self):
		"""删除内层独立pad"""

		self.COM('chklist_single,action=valor_dfm_nfpr,show=yes')
		self.COM('chklist_erf,chklist=valor_dfm_nfpr,nact=1,erf=Del Isolated')
		self.COM('chklist_cupd,chklist=valor_dfm_nfpr,nact=1,params=((pp_layer=.type=signal|mixed&context=board&side=inner)(pp_delete=Isolated)(pp_work=Features)(pp_drill=PTH\;NPTH\;Via\;PTH - Pressfit\;Via - Laser\;Via - Photo)(pp_non_drilled=Yes)(pp_in_selected=All)(pp_remove_mark=Remove)),mode=regular')
		self.COM('chklist_run,chklist=valor_dfm_nfpr,nact=1,area=profile')
		self.COM('chklist_close,chklist=valor_dfm_nfpr,mode=hide')

	def padSnapping(self, referLayer:str):
		"""对齐"""
		if self.unit == 'mm':
			self.COM('chklist_single,action=valor_dfm_pad_snap,show=yes')
			self.COM('chklist_erf,chklist=valor_dfm_pad_snap,nact=1,erf=Affected Layers (Microns)')
			self.COM('chklist_cupd,chklist=valor_dfm_pad_snap,nact=1,params=((pp_layer=.affected)(pp_snap_to=Ref Layer)(pp_ref_layer=%s)(pp_grid_value_x=2.54)(pp_grid_value_y=2.54)(pp_origin_x=0)(pp_origin_y=0)(pp_max_snapping=50.8)(pp_max_report=254)(pp_min_spacing=127)(pp_ignore_attr=.bga)(pp_ignore_drill_attr=)(pp_include_smds=No)),mode=regular' % referLayer)
			self.COM('chklist_run,chklist=valor_dfm_pad_snap,nact=1,area=profile')
			self.COM('chklist_close,chklist=valor_dfm_pad_snap,mode=hide')

	def selectedFeaturesResize(self, size:float):
		"""补偿"""

		self.COM(f'sel_resize,size={str(size):s},corner_ctl=no')

	def affectedLayersPadUp(self, pthMin:float, pthOpt:float, viaMin:float, viaOpt:float, showResult:bool=False):
		"""涨pad"""

		if self.unit == 'mm':
			self.COM('chklist_single,action=valor_dfm_sigopt,show=yes')
			self.COM('chklist_erf,chklist=valor_dfm_sigopt,nact=1,erf=affected-1OZ---PadUP')
			self.COM('chklist_cupd,chklist=valor_dfm_sigopt,nact=1,params=((pp_layer=.affected)(pp_min_pth_ar=%s)(pp_opt_pth_ar=%s)(pp_min_via_ar=%s)(pp_opt_via_ar=%s)(pp_min_spacing=2.54)(pp_opt_spacing=2.54)(pp_min_p2p_spacing=2.54)(pp_opt_p2p_spacing=2.54)(pp_min_line=101.6)(pp_opt_line=254)(pp_nd_percent=10)(pp_abs_min_line=127)(pp_min_pth2c=25.4)(pp_selected=All)(pp_work_on=Pads\;SMDs\;Drills)(pp_modification=PadUp)),mode=regular' % (str(pthMin),str(pthOpt),str(viaMin),str(viaOpt)))
			self.COM('chklist_run,chklist=valor_dfm_sigopt,nact=1,area=profile')
			if showResult:
				self.COM('chklist_res_show,chklist=valor_dfm_sigopt,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_dfm_sigopt,mode=hide')

	def affectedLayersShavePad(self, pthMin:float, pthOpt:float, viaMin:float, viaOpt:float, spaceMin:float, spaceOpt:float, showResult:bool=False):
		"""影响层削pad"""

		if self.unit == 'mm':
			self.COM('chklist_single,action=valor_dfm_sigopt,show=yes')
			self.COM('chklist_erf,chklist=valor_dfm_sigopt,nact=1,erf=affected-1OZ-ShavePad')
			self.COM('chklist_cupd,chklist=valor_dfm_sigopt,nact=1,params=((pp_layer=.affected)(pp_min_pth_ar=%s)(pp_opt_pth_ar=%s)(pp_min_via_ar=%s)(pp_opt_via_ar=%s)(pp_min_spacing=%s)(pp_opt_spacing=%s)(pp_min_p2p_spacing=%s)(pp_opt_p2p_spacing=%s)(pp_min_line=101.6)(pp_opt_line=254)(pp_nd_percent=10)(pp_abs_min_line=127)(pp_min_pth2c=256.54)(pp_selected=All)(pp_work_on=Pads\;SMDs\;Drills)(pp_modification=Shave)),mode=regular' % (str(pthMin),str(pthOpt),str(viaMin),str(viaOpt),str(spaceMin),str(spaceOpt),str(spaceMin),str(spaceOpt)))
			self.COM('chklist_run,chklist=valor_dfm_sigopt,nact=1,area=profile')
			if showResult:
				self.COM('chklist_res_show,chklist=valor_dfm_sigopt,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_dfm_sigopt,mode=hide')

	def miLayersAnalyze(self):
		"""mi线路分析"""

		if self.unit == 'mm':
			self.COM('chklist_single,action=valor_analysis_signal,show=yes')
			self.COM('chklist_erf,chklist=valor_analysis_signal,nact=1,erf=MI Check')
			self.COM('chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer=.type=signal|mixed&context=board)(pp_spacing=508)(pp_r2c=508)(pp_d2c=508)(pp_sliver=254)(pp_min_pad_overlap=127)(pp_tests=Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;SMD\;Bottleneck\;Pad Connection Check)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular')
			self.COM('chklist_run,chklist=valor_analysis_signal,nact=1,area=profile')
			self.COM('chklist_res_show,chklist=valor_analysis_signal,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_analysis_signal,mode=hide')

	def innerLayersAnalyze(self, showResult:bool=True, exportAll:bool=False):
		"""内层线路分析"""

		if self.unit == 'mm':
			self.COM('chklist_single,action=valor_analysis_signal,show=yes')
			self.COM('chklist_erf,chklist=valor_analysis_signal,nact=1,erf=Inner')
			self.COM('chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer=.type=signal|mixed&side=inner)(pp_spacing=254)(pp_r2c=381)(pp_d2c=304.8)(pp_sliver=127)(pp_min_pad_overlap=127)(pp_tests=Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;Bottleneck\;Pad Connection Check)(pp_selected=All)(pp_check_missing_pads_for_drills=No)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular')
			self.COM('chklist_run,chklist=valor_analysis_signal,nact=1,area=profile')
			if showResult:
				self.COM('chklist_res_show,chklist=valor_analysis_signal,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_analysis_signal,mode=hide')
			if exportAll:
				self.COM(f'chklist_res_exp,chklist=valor_analysis_signal,nact=0,source=all,dest=file,fname={self.tmp:s}')
				with open(self.tmpfile, 'r', encoding='iso-8859-15') as file:
					infoList = file.readlines()
				os.unlink(self.tmpfile)

				return self.parseInfoToDict(infoList)

	def outerLayersAnalyze(self, showResult:bool=True, exportAll:bool=False):
		"""外层线路分析"""

		if self.unit == 'mm':
			self.COM('chklist_single,action=valor_analysis_signal,show=yes')
			self.COM('chklist_erf,chklist=valor_analysis_signal,nact=1,erf=Outer')
			self.COM('chklist_cupd,chklist=valor_analysis_signal,nact=1,params=((pp_layer=.type=signal|mixed&side=top|bottom)(pp_spacing=254)(pp_r2c=381)(pp_d2c=304.8)(pp_sliver=254)(pp_min_pad_overlap=127)(pp_tests=Spacing\;Drill\;Rout\;Size\;Sliver\;Stubs\;Center\;SMD\;Bottleneck\;Pad Connection Check)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular')
			self.COM('chklist_run,chklist=valor_analysis_signal,nact=1,area=profile')
			if showResult:
				self.COM('chklist_res_show,chklist=valor_analysis_signal,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_analysis_signal,mode=hide')
			if exportAll:
				self.COM(f'chklist_res_exp,chklist=valor_analysis_signal,nact=0,source=all,dest=file,fname={self.tmp:s}')
				with open(self.tmpfile, 'r', encoding='iso-8859-15') as file:
					infoList = file.readlines()
				os.unlink(self.tmpfile)

				return self.parseInfoToDict(infoList)

	def getCopperArea(self, layer1:str, layer2:str, thickness:str):
		"""获取电镀面积,只能同时填一个"""

		if self.unit == 'mm':
			self.COM(f'copper_area,layer1={layer1:s},layer2={layer2:s},drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness={thickness:s},resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
			return self.COMANS

	def createDrlMap(self, layer:str, mapLayer:str, preserveAttr:str='no', drawOrigin:str='no', defineViaType:str='yes', units:str='mm', markDim:float=2000, markLineWidth:float=200, markLocation:str='center', sr:str='no', slots:str='by_length', columns:str='Tool|Count|Type|Finish', notype:str='plt', tablePos:str='right', tableAlign:str='bottom', sortBy:str='tool', sortDir:str='incr'):
		"""创建分孔图"""

		columns = columns.replace('|','\;')
		self.COM(f'cre_drills_map,layer={layer:s},map_layer={mapLayer:s},preserve_attr={preserveAttr:s},draw_origin={drawOrigin:s},define_via_type={defineViaType:s},units={units:s},mark_dim={str(markDim):s},mark_line_width={str(markLineWidth):s},mark_location={markLocation:s},sr={sr:s},slots={slots:s},columns={columns:s},notype={notype:s},table_pos={tablePos:s},table_align={tableAlign:s},sort_by={sortBy:s},sort_dir={sortDir:s}')

	def netAnalyze(self, stepName:str, isClose:bool=True):
		"""网络分析"""

		self.COM('netlist_page_open,set=check,job1=%s,step1=edit,type1=ref,job2=%s,step2=edit,type2=cur' % (self.job.name, self.job.name))
		self.COM('netlist_recalc,job=%s,step=%s,type=cur,display=top,layer_list=' % (self.job.name,stepName))
		self.COM('netlist_recalc,job=%s,step=%s,type=cur,display=bottom,layer_list=' % (self.job.name, self.name))
		self.COM('netlist_compare,job1=%s,step1=%s,type1=cur,job2=%s,step2=%s,type2=cur,display=yes,filter_ignore_net_names=no,filter_cad_problem=no,filter_nfp=no,filter_attr_diff=no,filter_extra_on_pad=no,filter_backdrill=no' % (self.job.name, stepName, self.job.name, self.name))
		if isClose:
			self.COM('netlist_page_close')

	def ipcNetAnalyze(self,isClose=False):
		"""ipc网络分析"""

		self.COM('netlist_page_open,set=check,job1=%s,step1=orig,type1=ref,job2=%s,step2=orig,type2=cur' % (self.job.name, self.job.name))
		self.COM('netlist_recalc,job=%s,step=orig,type=cad,display=top,layer_list=' % self.job.name)
		self.COM('netlist_recalc,job=%s,step=orig,type=cur_cad,display=bottom,layer_list=' % self.job.name)
		self.COM('netlist_compare,job1=%s,step1=orig,type1=cad,job2=%s,step2=orig,type2=cur_cad,display=yes,filter_ignore_net_names=no,filter_cad_problem=no,filter_nfp=no,filter_attr_diff=no,filter_extra_on_pad=no,filter_backdrill=no' % (self.job.name, self.job.name))
		if isClose:
			self.COM('netlist_page_close')

	def solderOptimize(self, side:str, spaceMinimum:float, spaceOptimum:float, coverMinimum:float, coverOptimum:float, solderBridge:float, showResult:bool=True):
		"""阻焊优化"""

		self.COM('chklist_single,action=valor_dfm_smcc,show=yes')
		self.COM('chklist_erf,chklist=valor_dfm_smcc,nact=1,erf=3.0/3.0--3.0/3.0--4(Mils)')
		self.COM('chklist_cupd,chklist=valor_dfm_smcc,nact=1,params=((pp_layer=.type=signal|mixed&side=%s)(pp_min_clear=%s)(pp_opt_clear=%s)(pp_min_cover=%s)(pp_opt_cover=%s)(pp_bridge=%s)(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)),mode=regular' % (side, str(spaceMinimum), str(spaceOptimum), str(coverMinimum), str(coverOptimum), str(solderBridge)))
		self.COM('chklist_run,chklist=valor_dfm_smcc,nact=1,area=profile')
		if showResult:
			self.COM('chklist_res_show,chklist=valor_dfm_smcc,nact=1,x=150,y=100,w=500,h=700')
		self.COM('chklist_close,chklist=valor_dfm_smcc,mode=hide')

	def solderAnalyze(self):
		"""阻焊分析"""

		if self.unit == 'inch':
			self.COM('chklist_single,action=valor_analysis_sm,show=yes')
			self.COM('chklist_cupd,chklist=valor_analysis_sm,nact=1,params=((pp_layers=.type=solder_mask&context=board)(pp_ar=4)(pp_coverage=4)(pp_sm2r=10)(pp_sliver=8)(pp_spacing=8)(pp_bridge=8)(pp_min_clear_overlap=5)(pp_tests=Drill\;Pads\;Coverage\;Bridge\;Sliver\;Missing\;Spacing\;Clearance Connection)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
			self.COM('chklist_run,chklist=valor_analysis_sm,nact=1,area=profile')
			self.COM('chklist_res_show,chklist=valor_analysis_sm,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_analysis_sm,mode=hide')
		elif self.unit == 'mm':
			self.COM('chklist_single,action=valor_analysis_sm,show=yes')
			self.COM('chklist_cupd,chklist=valor_analysis_sm,nact=1,params=((pp_layers=.type=solder_mask&context=board)(pp_ar=101.6)(pp_coverage=101.6)(pp_sm2r=254)(pp_sliver=203.2)(pp_spacing=203.2)(pp_bridge=203.2)(pp_min_clear_overlap=127)(pp_tests=Drill\;Pads\;Coverage\;Bridge\;Sliver\;Missing\;Spacing\;Clearance Connection)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
			self.COM('chklist_run,chklist=valor_analysis_sm,nact=1,area=profile')
			self.COM('chklist_res_show,chklist=valor_analysis_sm,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_analysis_sm,mode=hide')

	def solderAnalyzeBefore(self):
		"""处理前阻焊分析"""

		self.COM('chklist_single,action=valor_analysis_sm,show=yes')
		self.COM('chklist_cupd,chklist=valor_analysis_sm,nact=1,params=((pp_layers=.type=solder_mask&context=board)(pp_ar=4)(pp_coverage=4)(pp_sm2r=10)(pp_sliver=8)(pp_spacing=8)(pp_bridge=8)(pp_min_clear_overlap=5)(pp_tests=Pads)(pp_selected=All)(pp_use_compensated_rout=No)),mode=regular')
		self.COM('chklist_run,chklist=valor_analysis_sm,nact=1,area=profile')
		self.COM('chklist_res_show,chklist=valor_analysis_sm,nact=1,x=150,y=100,w=500,h=700')
		self.COM('chklist_close,chklist=valor_analysis_sm,mode=hide')

	"""
	钻孔相关
	"""

	def toolsMerge(self, layerName:str, mode:str='merge'):
		"""合并相同的tools"""

		self.COM(f'tools_merge_ex,layer={layerName:s},mode={mode:s}')

	def deleteDuplicateForAffectedLayers(self):
		"""删除重叠的features"""

		self.COM(f'chklist_single,action=valor_dfm_nfpr,show=yes')
		self.COM(f'chklist_erf,chklist=valor_dfm_nfpr,nact=1,erf=Del Duplicate')
		self.COM(f'chklist_cupd,chklist=valor_dfm_nfpr,nact=1,params=((pp_layer=.affected)(pp_delete=Duplicate)(pp_work=Features)(pp_drill=PTH\;NPTH\;Via\;PTH - Pressfit\;Via - Laser\;Via - Photo)(pp_non_drilled=No)(pp_in_selected=All)(pp_remove_mark=Remove)),mode=regular')
		self.COM(f'chklist_run,chklist=valor_dfm_nfpr,nact=1,area=profile')
		self.COM(f'chklist_close,chklist=valor_dfm_nfpr,mode=hide')

	def drillAnalyze(self):
		"""钻孔分析"""

		if self.unit == 'inch':
			self.COM('chklist_single,action=valor_analysis_drill,show=yes')
			self.COM('chklist_cupd,chklist=valor_analysis_drill,nact=1,params=((pp_drill_layer=.type=drill&context=board)(pp_rout_distance=200)(pp_tests=Hole Size\;Hole Separation\;Missing Holes\;Extra Holes\;Power/Ground Shorts\;NPTH to Rout)(pp_extra_hole_type=Pth\;Via)(pp_use_compensated_rout=Skeleton)),mode=regular')
			self.COM('chklist_run,chklist=valor_analysis_drill,nact=1,area=profile')
			self.COM('chklist_res_show,chklist=valor_analysis_drill,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_analysis_drill,mode=hide')
		elif self.unit == 'mm':
			self.COM('chklist_single,action=valor_analysis_drill,show=yes')
			self.COM('chklist_cupd,chklist=valor_analysis_drill,nact=1,params=((pp_drill_layer=.type=drill&context=board)(pp_rout_distance=5080)(pp_tests=Hole Size\;Hole Separation\;Missing Holes\;Extra Holes\;Power/Ground Shorts\;NPTH to Rout)(pp_extra_hole_type=Pth\;Via)(pp_use_compensated_rout=Skeleton)),mode=regular')
			self.COM('chklist_run,chklist=valor_analysis_drill,nact=1,area=profile')
			self.COM('chklist_res_show,chklist=valor_analysis_drill,nact=1,x=150,y=100,w=500,h=700')
			self.COM('chklist_close,chklist=valor_analysis_drill,mode=hide')

	def drillToolsSet(self, drillTools:list=[], userParameter:str='hasl'):
		"""
		设置钻孔表
		@param drillTools: 钻孔工具表<list>
		@param userParameter: 用户名<str>/hasl/osp
		@return:
		"""

		# 辅助字典
		assistDict = {'plated':'plate', 'non_plated':'nplate', 'via':'via'}
		self.COM('tools_tab_reset')
		for row in drillTools:
			self.COM(f'tools_tab_add,num={row.number:d},shape={row.shape:s},type={assistDict[row.type]:s},min_tol={str(row.minTol):s},max_tol={str(row.maxTol):s},bit={row.bit:s},finish_size={str(row.finishSize):s},drill_size={str(row.drillSize):s},slot_len={str(row.slotLength):s}')
		self.COM(f'tools_set,layer=drl,thickness=0,user_params={userParameter:s},slots=by_length')

	def clipArea(self, layersMode:str='affected_layers', clipLayerName:str='', area:str='reference', referLayerName:str='', inOut:str='inside', margin:float=0, featTypes:str='line|pad|surface|arc|text', contourCut:str='no'):
		"""
		剪切区域
		@param layersMode: 层模式<str>/affected_layers:影响层/layer_name:层名
		@param clipLayerName:修剪层<str>
		@param area:参考方式<str>/reference:物件/profile:轮廓
		@param referLayerName:参考层<str>
		@param inOut: 内或外<str>/内侧:inside/外侧:outside
		@param margin:差额<float>
		@param featTypes:修剪的物件<str>
		@param contourCut:是否转化为铜皮<str>/no/yes
		@return:
		"""

		featTypes = featTypes.replace("|", "\;")
		self.COM('clip_area_strt')
		self.COM(f'clip_area_end,layers_mode={layersMode:s},layer={clipLayerName:s},area={area:s},area_type=rectangle,inout={inOut:s},contour_cut={contourCut:s},margin={margin:f},ref_layer={referLayerName:s},feat_types={featTypes:s}')

	def fillParams(self, minBrush:float):
		"""fill"""

		if self.unit == 'inch':
			self.COM(f'fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush={str(minBrush):s},use_arcs=yes,symbol=,dx=0.1,dy=0.1,x_off=0,y_off=0,std_angle=45,std_line_width=1,std_step_dist=50,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no')
			self.COM('sel_fill')
		elif self.unit == 'mm':
			self.COM(f'fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush={str(minBrush):s},use_arcs=yes,symbol=,dx=2.54,dy=2.54,x_off=0,y_off=0,std_angle=45,std_line_width=25.4,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no')
			self.COM('sel_fill')

	def selTransform(self, xAnchor:float, yAnchor:float, xScale:float, yScale:float):
		"""比例缩放"""

		self.COM('sel_transform,mode=anchor,oper=scale,duplicate=no,x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=0,y_offset=0' % (str(xAnchor),str(yAnchor),str(xScale),str(yScale)))

	def selTransformRotate(self, xAnchor:float, yAnchor:float, angle:float):
		"""旋转"""

		self.COM('sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor=%s,y_anchor=%s,angle=%s,x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (str(xAnchor),str(yAnchor),str((360 - angle) % 360)))

	def selCleanHoles(self):
		"""清除铜皮孔"""

		self.COM('sel_clean_holes,max_size=8000,clean_mode=x_and_y')

	def selectedFeaturesCreateSymbol(self, symbol:str, xDatum:float, yDatum:float):
		"""创建symbol"""

		self.COM('sel_create_sym,symbol=%s,x_datum=%s,y_datum=%s,delete=no,fill_dx=0.1,fill_dy=0.1,attach_atr=no,retain_atr=no' % (symbol,str(xDatum),str(yDatum)))

	def selSubstitute(self, symbol:str, xDatum:float, yDatum:float):
		"""替换symbol"""

		self.COM('sel_substitute,mode=substitute,symbol=%s,tol=1,x_datum=%s,y_datum=%s,dcode=0' % (symbol,str(xDatum),str(yDatum)))

	def selBreak(self):
		"""break"""

		self.COM('sel_break')

	def selectedSlotsExtend(self, size:float, mode:str= 'ext_by', fromPoint:str= 'center'):
		"""拉长线和pad,单位：um/mil;start,end,center, 以上为不动的点"""

		self.COM(f'sel_extend_slots,mode={mode:s},size={str(size):s},from={fromPoint:s}')

	"""
	输出资料相关
	"""
	def printPdf(self, title:str='', layersName:list=[], mirroredLayers:list=[], drawProfile:str='no', drawingPerLayer:str='yes', labelLayers:str='no', destFname:str='', paperSize:str='A4', orient:str='none', paperOrient:str='portrait', pageNumbering:str='no', topMargin:str='0', bottomMargin:str='0', leftMargin:str='0', rightMargin:str='0', color1:str='990000', color2:str='99', color3:str='9900', color4:str='990099', color5:str='999900', color6:str='9999'):
		"""
		打印pdf
		@param title: 标题<str>
		@param layersName: 层名<list>
		@param mirroredLayers: 镜像层名<list>
		@param drawProfile: 打印profile<str>/yes:打印/no:不打印
		@param drawingPerLayer: 是否单独打印层<str>/yes:单独/no:重叠
		@param labelLayers: 层名label位置<str>
		@param destFname: 输出路径<str>
		@param paperSize: 输出尺寸<str>/A4/A1
		@param orient: 方向<str>/landscape:水平/portrait:竖直/none:自行
		@param paperOrient: 方向<str>/landscape:水平/portrait:竖直
		@param pageNumbering:页码<str>/yes/no
		@param topMargin:边缘间距（下同）
		@param bottomMargin:
		@param leftMargin:
		@param rightMargin:
		@param color1:颜色（下同）
		@param color2:
		@param color3:
		@param color4:
		@param color5:
		@param color6:
		@return:
		"""

		self.COM(f'print,title={title:s},layer_name={";".join(layersName):s},mirrored_layers={";".join(mirroredLayers):s},draw_profile={drawProfile:s},drawing_per_layer={drawingPerLayer:s},label_layers={labelLayers:s},dest=pdf_file,num_copies=1,dest_fname={destFname:s},paper_size={paperSize:s},scale_to=0,nx=1,ny=1,orient={orient:s},paper_orient={paperOrient:s},paper_width=0,paper_height=0,paper_units=inch,auto_tray=no,page_numbering={pageNumbering:s},top_margin={topMargin:s},bottom_margin={bottomMargin:s},left_margin={leftMargin:s},right_margin={rightMargin:s},x_spacing=0,y_spacing=0,color1={color1:s},color2={color2:s},color3={color3:s},color4={color4:s},color5={color5:s},color6={color6:s}')

	def outPutGerber(self, job:str, step:str, layers:str, dirPath:str, prefix:str='', suffix:str='',xscale:float=1, yscale:float=1):
		"""输出gerber"""

		self.COM('output_layer_reset')
		for layer in layers.split('|'):
			self.COM(f'output_layer_set,layer={layer:s},angle=0,mirror=no,x_scale={xscale},y_scale={yscale},comp=0,polarity=positive,setupfile=,setupfiletmp=,'
					 f'line_units=mm,gscl_file=,step_scale=no')
		self.COM(f'output,job={job:s},step={step:s},format=Gerber274x,dir_path={dirPath:s},prefix={prefix:s},suffix={suffix:s},break_sr=yes,'
				 f'break_symbols=yes,break_arc=yes,scale_mode=all,surface_mode=contour,min_brush=1,units=mm,coordinates=absolute,'
				 f'zeroes=trailing,nf1=3,nf2=5,x_anchor=0,y_anchor=0,wheel=,x_offset=0,y_offset=0,line_units=mm,override_online=yes,'
				 f'film_size_cross_scan=0,film_size_along_scan=0,ds_model=RG6500')

	def outPutExcellon2(self, job:str, step:str, layers:str, dirPath:str, prefix:str='', suffix:str='',xscale:float=1, yscale:float=1):
		"""输出锣带"""

		self.COM('output_layer_reset')
		for layer in layers.split('|'):
			self.COM(f'output_layer_set,layer={layer:s},angle=0,mirror=no,x_scale={xscale},y_scale={yscale},comp=0,polarity=positive,setupfile=,setupfiletmp=,line_units=inch,gscl_file=,step_scale=no')
		self.COM(f'output,job={job:s},step={step:s},format=Excellon2,dir_path={dirPath:s},prefix={prefix:s},suffix={suffix:s},break_sr=yes,break_symbols=yes,break_arc=no,scale_mode=all,surface_mode=fill,min_brush=1,units=mm,coordinates=absolute,decimal=no,zeroes=trailing,nf1=3,nf2=3,modal=yes,tool_units=mm,optimize=yes,iterations=5,reduction_percent=1,cool_spread=0,x_anchor=0,y_anchor=0,x_offset=0,y_offset=0,line_units=mm,override_online=yes,canned_text_mode=break')

	def outPutDxf(self, job:str, step:str, layers:str,mirrors:str='',dirPath:str='', prefix:str='', suffix:str='',xscale:float=1, yscale:float=1):
		"""输出dxf"""

		self.COM('output_layer_reset')
		for layer in layers.split('|'):
			self.COM(f'output_layer_set,layer={layer:s},angle=0,mirror={mirrors},x_scale={xscale},y_scale={yscale},comp=0,polarity=positive,setupfile=,setupfiletmp=,line_units=inch,gscl_file=,step_scale=no')
		self.COM(f'output,job={job:s},step={step:s},format=DXF,dir_path={dirPath:s},prefix={prefix:s},suffix={suffix:s},break_sr=yes,break_symbols=yes,break_arc=no,scale_mode=all,surface_mode=fill,min_brush=1,units=mm,x_anchor=0,y_anchor=0,x_offset=0,y_offset=0,line_units=mm,override_online=yes,pads_2circles=yes,draft=no,contour_to_hatch=no,pad_outline=yes,output_files=multiple,file_ver=autocad2002')

	def exportJob(self, job:str, path:str):
		"""导出料号"""

		self.COM(f'export_job,job={job:s},path={path:s},mode=tar_gzip,submode=full,overwrite=yes,analyze_surfaces=no')

	"""SR相关"""
	def flattenLayer(self, sourceLayer:str, targetLayer:str):
		"""set实体化,如果存在层会覆盖"""

		self.COM('flatten_layer,source_layer=%s,target_layer=%s' % (sourceLayer, targetLayer))

	def addSrTable(self, line:str, step:str, point:Point, nx:str='1', ny:str='1', dx:str='0', dy:str='0', angle:str= '0', mirror:str= 'no'):
		"""添加table, line：行"""

		self.COM('sr_tab_add,line=%s,step=%s,x=%s,y=%s,nx=%s,ny=%s,dx=%s,dy=%s,angle=%s,mirror=%s' % (line, step, str(point.x), str(point.y), nx, ny, dx, dy, angle, mirror))

	def changeSrTable(self, line:str, step:str, point:Point, nx:str='1', ny:str='1', dx:str='0', dy:str='0', angle:str= '0', mirror:str= 'no'):
		"""改变table"""

		self.COM('sr_tab_change,line=%s,step=%s,x=%s,y=%s,nx=%s,ny=%s,dx=%s,dy=%s,angle=%s,mirror=%s' % (line, step, str(point.x), str(point.y), nx, ny, dx, dy, angle, mirror))

	def srEdit(self, display:bool=False):
		"""sr编辑器"""

		if display:
			self.COM('sredit_popup')
		else:
			self.COM('sredit_close')

	def origin(self, point:Point):
		"""绝对零点"""

		self.COM(f'origin,x={point.x:.10f},y={point.y:.10f},push_in_stack=1')

	def datum(self, point:Point):
		"""相对零点"""

		self.COM(f'datum,x={str(point.x):s},y={str(point.y):s}')


class MatrixCommands:
	"""matrix指令"""

	def getRow(self, rowName:str='', rowNumber:int=0):
		"""层名序号互转"""

		if rowName and not rowNumber:
			for item in self.row:
				if item.name == rowName:
					return item.row
			return None

		elif rowNumber and not rowName:
			for item in self.row:
				if item.row == rowNumber:
					return item.name
			return None

	def isRowExist(self, rowName:str='', rowNumber:int=0) -> bool:
		"""层名判断层存在"""

		if rowName and not rowNumber:
			if self.getRow(rowName=rowName):
				return True
			else:
				return False

		if rowNumber and not rowName:
			if self.getRow(rowNumber=rowNumber) == None:
				return False
			else:
				return True

	def deleteRow(self, rowName:str='', rowNumber:int=0):
		"""删除单行"""

		if rowName and not rowNumber:
			if self.isRowExist(rowName=rowName):
				self.job.COM('matrix_delete_row,job=%s,row=%d,matrix=matrix' % (self.job.name, self.getRow(rowName=rowName)))

		elif rowNumber and not rowName:
			if self.isRowExist(rowNumber=rowNumber):
				self.job.COM('matrix_delete_row,job=%s,row=%d,matrix=matrix' % (self.job.name, rowNumber))

	def copyRow(self, newName:str, insertRowNumber:int, rowName:str='', rowNumber:int=0, context:str= 'misc', rowType:str= 'document'):
		"""复制单层到指定行"""

		if rowName and not rowNumber:
			if self.isRowExist(rowName=rowName):
				self.job.COM('matrix_copy_row,job=%s,row=%d,matrix=matrix,ins_row=%d' % (self.job.name, self.getRow(rowName=rowName), insertRowNumber))
				rowNameAssist = self.getRow(rowNumber=insertRowNumber)
				if rowNameAssist != newName:
					self.deleteRow(rowName=newName)
				self.job.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=%s' % (self.job.name, rowNameAssist, context))
				self.job.COM('matrix_layer_type,job=%s,matrix=matrix,layer=%s,type=%s' % (self.job.name, rowNameAssist, rowType))
				self.job.COM('matrix_rename_layer,job=%s,matrix=matrix,layer=%s,new_name=%s' % (self.job.name, rowNameAssist, newName))

		elif rowNumber and not rowName:
			if self.isRowExist(rowNumber=rowNumber):
				self.job.COM('matrix_copy_row,job=%s,row=%d,matrix=matrix,ins_row=%d' % (self.job.name, rowNumber, insertRowNumber))
				rowNameAssist = self.getRow(rowNumber=insertRowNumber)
				if rowNameAssist != newName:
					self.deleteRow(rowName=newName)
				self.job.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=%s' % (self.job.name, rowNameAssist, context))
				self.job.COM('matrix_layer_type,job=%s,matrix=matrix,layer=%s,type=%s' % (self.job.name, rowNameAssist, rowType))
				self.job.COM('matrix_rename_layer,job=%s,matrix=matrix,layer=%s,new_name=%s' % (self.job.name, rowNameAssist, newName))

	def modifyRow(self, currentName:str='', currentRowNumber:int=0, newName:str='', insertRowNumber:int=0, context:str='', rowType:str= '', polarity:str= ''):
		"""修改层信息"""

		if currentName and not currentRowNumber:
			if insertRowNumber:
				self.job.COM('matrix_move_row,job=%s,matrix=matrix,row=%d,ins_row=%d' % (self.job.name, self.getRow(rowName=currentName), insertRowNumber))
			if context:
				self.job.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=%s' % (self.job.name, currentName, context))
			if rowType:
				self.job.COM('matrix_layer_type,job=%s,matrix=matrix,layer=%s,type=%s' % (self.job.name, currentName, rowType))
			if polarity:
				self.job.COM('matrix_layer_polar,job=%s,matrix=matrix,layer=%s,polarity=%s' % (self.job.name, currentName, polarity))
			if newName:
				if currentName != newName:
					self.deleteRow(rowName=newName)
				self.job.COM('matrix_rename_layer,job=%s,matrix=matrix,layer=%s,new_name=%s' % (self.job.name, currentName, newName))

		elif currentRowNumber and not currentName:
			rowNameAssist = self.getRow(rowNumber=currentRowNumber)
			if insertRowNumber:
				self.job.COM('matrix_move_row,job=%s,matrix=matrix,row=%d,ins_row=%d' % (self.job.name, currentRowNumber, insertRowNumber))
			if context:
				self.job.COM('matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=%s' % (self.job.name, rowNameAssist, context))
			if rowType:
				self.job.COM('matrix_layer_type,job=%s,matrix=matrix,layer=%s,type=%s' % (self.job.name, rowNameAssist, rowType))
			if polarity:
				self.job.COM('matrix_layer_polar,job=%s,matrix=matrix,layer=%s,polarity=%s' % (self.job.name, rowNameAssist, polarity))
			if newName:
				if rowNameAssist != newName:
					self.deleteRow(rowName=newName)
				self.job.COM('matrix_rename_layer,job=%s,matrix=matrix,layer=%s,new_name=%s' % (self.job.name, rowNameAssist, newName))

	def returnRows(self, context:str='', layerType:str='', polarity:str='', side:str='', returnName:bool=True) -> list:
		"""返回上述条件满足的行序号或者名字,用|分割多个选项，或关系"""

		# 分割条件
		contextList = context.split('|')
		typeList = layerType.split('|')
		polarityList = polarity.split('|')
		sideList = side.split('|')

		rowList = []
		nameList = []

		for x in range(len(self.row)):
			if self.row[x].name == '':
				continue
			if self.row[x].type != 'layer':
				continue
			if context:
				if self.row[x].context in contextList:
					pass
				else:
					continue
			if layerType:
				if self.row[x].layerType in typeList:
					pass
				else:
					continue
			if polarity:
				if self.row[x].polarity in polarityList:
					pass
				else:
					continue
			if side:
				if self.row[x].side in sideList:
					pass
				else:
					continue
			rowList.append(self.row[x].row)
			nameList.append(self.row[x].name)

		if returnName:
			return nameList
		else:
			return rowList

	def removeEmptyRows(self):
		"""清除空行"""

		flag = True
		while flag:
			for item in self.row:
				if item.type == 'empty':
					self.job.COM('matrix_delete_row,job=%s,row=%d,matrix=matrix' % (self.job.name, item.row))
					break
			else:
				flag = False

	def getColumn(self, columnName:str= '', columnNumber:int= 0):
		"""列名序号互转"""

		if columnName and not columnNumber:
			for item in self.column:
				if item.name == columnName:
					return item.column
			return None

		elif columnNumber and not columnName:
			for item in self.column:
				if item.column == columnNumber:
					return item.name
			return None

	def isColumnExist(self, columnName:str='', columnNumber:int=0) -> bool:
		"""列名判断列存在"""

		if columnName and not columnNumber:
			if self.getColumn(columnName=columnName):
				return True
			else:
				return False

		if columnNumber and not columnName:
			if self.getColumn(columnNumber=columnNumber) == None:
				return False
			else:
				return True

	def deleteColumn(self, columnName:str= '', columnNumber:int= 0):
		"""删除单列"""

		if columnName and not columnNumber:
			if self.isColumnExist(columnName=columnName):
				self.job.COM('matrix_delete_col,job=%s,matrix=matrix,col=%d' % (self.job.name, self.getColumn(columnName=columnName)))

		elif columnNumber and not columnName:
			if self.isColumnExist(columnNumber=columnNumber):
				self.job.COM('matrix_delete_col,job=%s,matrix=matrix,col=%d' % (self.job.name, columnNumber))

	def copyStep(self, columnName:str, toName:str, insertColumn:int):
		"""复制step"""

		if self.isColumnExist(columnName=columnName):
			self.job.COM('matrix_copy_col,job=%s,matrix=matrix,col=%d,ins_col=%d' % (self.job.name, self.getColumn(columnName=columnName), insertColumn))
			columnAssist = self.getColumn(columnNumber=insertColumn)
			if columnAssist != toName:
				self.deleteColumn(columnName=toName)
			self.job.COM('matrix_rename_step,job=%s,matrix=matrix,step=%s,new_name=%s' % (self.job.name, columnAssist, toName))
