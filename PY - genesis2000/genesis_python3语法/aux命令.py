#!python3
import Genesis
g = Genesis.Genesis()

##获取料号和step
##g.PAUSE(g.JOB)
##g.PAUSE(g.STEP)


##设置当前step为操作单元
g.COM("open_entity,job={JOB},type=step,name={STEP},iconic=no"\
      .format(JOB=g.JOB,STEP=g.STEP))
g.AUX(g.COMANS)

##clear
g.COM("affected_layer,mode=all,affected=no")
g.COM("clear_layers")
g.COM("filter_reset,filter_name=popup")
g.COM("cur_atr_reset")
g.COM("clear_highlight")
g.COM("sel_clear_feat")


##错误跳过机制开关

g.VOF()
g.COM("delete_layer,layer=ts")
g.VON()

g.COM("display_layer,name=to,display=yes,number=1")
g.COM("work_layer,name=to")
g.COM("add_pad,attributes=no,x=0,y=0,symbol=r1000,polarity=positive,\
        angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1")

