#!python3


import Genesis 
g = Genesis.Genesis()

####读取方式2
##from Genesis import *
##g = Genesis()
##
####读取方式3
##import Genesis as G ##as后面表示的是把Genesis模块弄一个简化别名G
##g = G.Genesis()

'''

g.PAUSE(g.STATUS) #返回值0 or ***
g.PAUSE(g.COMANS)  ##返回值 详细结果

##获取单位
g.COM('get_units')

##获取影响层
g.COM("get_affect_layer")

##获取当前显示层,使用.split()分解成数组
g.COM("get_disp_layers")

g.COM("get_disp_layers").split()



##返回图形编辑器底部的消息框中的文本
g.COM("get_message_bar")

##aa=aa.split(',') #按,号分割成列表aa[0]
##aa=g.COM("get_message_bar").split(',') 
##aa=g.COM("get_message_bar").split(',') [1] #只要第二个元素


##获取图形原点
g.COM("get_origin") 
aa=g.COM("get_origin").split(' ')[0]


#该命令用于获取所选特征的数量
g.COM("get_select_count")

#该命令用于获取工作层的名称。如果没有工作层，则为空字符串
g.COM("get_work_layer")

#命令返回用户所属组的名称。
g.COM("get_user_group")



'''
#返回当前登录到系统中的用户名。
g.COM("get_user_name")

g.PAUSE(g.COMANS)  ##返回值inch or mm
