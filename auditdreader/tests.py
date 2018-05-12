import os, sys
from stat import *
import re

#mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime
def fun1():
    st = os.stat("./tesadasdat_file")
    print('fun1 end')

def fun2():
    print('fun2')
    fun1()
    print('fun2 end')

def fun3():
    print('fun3')
    fun2()
    print('fun3 end')

try:
    fun3()
except FileNotFoundError as err:
    print('Exception',err,' catched')