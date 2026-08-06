#!python3
import Genesis
g = Genesis.Genesis()


#g.COM('units,type=mm')

# g.PAUSE(g.get_units)  #获取单位 str
# g.PAUSE(g.get_affect_layer)   #获取影响层 ,数组[n,m]
# g.PAUSE(g.get_disp_layers)  #显示层,数组[n,m]
# g.PAUSE(g.get_message_bar)  #底部信息,数组[n,m]
# g.PAUSE(g.get_origin)  #原点[x,y]

# g.PAUSE(g.get_select_count)  #选中数量
# g.PAUSE(g.get_work_layer)
g.PAUSE(g.get_user_group)
g.PAUSE(g.get_user_name)