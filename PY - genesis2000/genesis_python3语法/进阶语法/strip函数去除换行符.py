#!python3
aa = 'dfsdf\n\n\n'
print(aa)
#1.手动去除最后一个字符串
print(aa[:-1]) 

#2.使用strip(),会去除换行符和空格等,
print(aa.strip())

#strip()只对结尾生效!!
bb = '111v 11122 \n'
print(bb)
print(bb.strip())
