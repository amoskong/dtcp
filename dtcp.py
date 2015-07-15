#!/usr/bin/python
# -*- coding: utf-8 -*-

import socket
import threading
import sys
import time
import getopt

def dataFormat(d,t):
  if t == 1: #将不可见字符格式化为点
    r = ''
    for c in d:
      if (ord(c) <= 31) or (ord(c) == 127):
        r += '.'
      else:
        r += c
    return r
  elif t == 2: #将所有字符格式化为ACSII码16进制形式
    r = ['%0*X' % (2,ord(c)) for c in d]
    return r
  else: #输入类型错误
    return False

def connecter(i,t,s,a):
  info = (("server","client"),('[DST->SRV]','[SRV->DST]'))
  try:
    while True:
      data = s.recv(buffSize)
      #如果本端关闭，则关闭对端socket
      if len(data) == 0:
        rLock = threading.RLock()
        rLock.acquire()
        #改变本组锁状态，使对端直接结束
        if threadList[i][2] == True:
          break
        threadList[i][2] = True
        rLock.release()
        print timeShower()+"[INFO] Tunnel %i closed by" % i,info[0][t]
        a.shutdown(socket.SHUT_RDWR)
        a.close()
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        break
      #将获取到的信息输出到对端
      print timeShower()+tunnelShower(i)+info[1][t],dataFormat(data,1)
      print dataFormat(data,2)
      a.sendall(data)
        
  except:
    pass
        
def isNum(s):
  #判断文本是否都为数字
  if len([c for c in s if c in '1234567890']) != len(s):
    return False
  else:
    return True

helpInfo = '''
dtcp is a tcp debug tool.

options:
  -s --srv : Srv address,it can be a port number or host:port
  -d --dst : Dst address,it can only be host:port
  -b -buff : Set the size of buff of srv and dst sockets
  -t : Show the time in every log
  -v : Show the tunnel number in evert log
  -h --help: Show help info
'''

if __name__ == '__main__':
  #初始化变量
  srvHost = False
  srvPort = False
  dstHost = False
  dstPort = False
  buffSize = 1024
  timeShower = lambda :''
  tunnelShower = lambda i:''
  #获取参数
  shortOptions = 'htvb:s:d:' #t:show time v:show tunnel b: s:srv d:dst b:buff
  longOptions = ['srv=','dst=','buff=','help']
  try:
    opts,args = getopt.getopt(sys.argv[1:],shortOptions,longOptions)
  except getopt.GetoptError,e:
    print(e)
    print 'Error,The program ended'
  for option,argument in opts:
    if option in ('-h','--help'):
      #帮助信息
      print helpInfo
      sys.exit(1)
    elif option in ('-s','--srv'):
      #源地址，可为端口号或"地址:端口"的形式，为端口时默认监听0.0.0.0
      srvHost = '0.0.0.0'
      if ':' in argument:
        srvHost = argument.split(':')[0]
        argument = argument.split(':')[1]
      if (isNum(argument) and (int(argument) not in range(0,65535))):
        print 'The port number for srv is wrong!'
        sys.exit(1)
      srvPort = int(argument)
    elif option in ('-d','--dst'):
      #目标地址，必须为"地址:端口"的形式
      if ':' in argument:
        dstHost = argument.split(':')[0]
        argument = argument.split(':')[1]
        if (isNum(argument) and (int(argument) not in range(0,65535))):
          print 'The port number for dst is wrong!'
          sys.exit(1)
        dstPort = int(argument)
      else:
        print 'The dst is wrong!'
        sys.exit(1)
    elif option in ('-b','buff'):
      #设定两边socket的buff大小
      if isNum(argument):
        buffSize = int(argument)
      else:
        print 'The buff size must be a number!'
        sys.exit(1)
    elif option in ('-t'):
      #是否显示时间
      timeShower = lambda :'[%i:%i:%i]' % time.localtime(time.time())[3:6]
    elif option in ('-v'):
      #是否显示Tunnel编号
      tunnelShower = lambda i:'[Tunnel %i]' % i
  #判断必要参数
  if srvPort == False:
    print 'srv port can\'t be NONE!'
    sys.exit(1)
  elif dstHost == False or dstPort == False:
    print 'dst address can\'t be NONE!'
    sys.exit(1)
  threadList = [] #线程列表
  #源地址开始监听本地端口
  srvSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  srvSocket.bind((srvHost,srvPort))
  srvSocket.listen(100)
  print 'The Program start'
  while True:
    try:
      conn,addr = srvSocket.accept()
    except:
      break
    print timeShower()+'[SRV] A connection from',addr[0],'with port',addr[1]
    #有连接过来时，先尝试连接目标服务器
    dstSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dstSocket.settimeout(5)
    try:
      dstSocket.connect((dstHost,dstPort))
      dstSocket.settimeout(None)
      print timeShower()+"[DST] Success connect to %s with port %i" % (dstHost,dstPort)
    except:
      print timeShower()+"[SRV] Connect to %s:%i failed" % (dstHost,dstPort)
      conn.shutdown(socket.SHUT_RDWR)
      conn.close()
      continue
    #将连接放入线程处理
    i = len(threadList)
    srvThread = threading.Thread(target=connecter,args=(i,1,conn,dstSocket))
    dstThread = threading.Thread(target=connecter,args=(i,0,dstSocket,conn))
    srvThread.start()
    dstThread.start()
    threadList.append([srvThread,dstThread,False])
    print timeShower()+'[INFO] Tunnel',i,'created'
  print "\nThe program ended"
  sys.exit(1)
