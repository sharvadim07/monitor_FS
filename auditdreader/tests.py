import os, sys
from stat import *
import re

#mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime
st = os.stat("./test_file")

#print(st.st_uid + ST_UID(st.st_uid) + S_ISDIR(st.st_mode) + ST_MTIME(st.st_mtime))

def name_from_path(path):
    str = re.match(r'(.*)[/]\w+$', path)
    st = os.stat(str.groups()[0])
    return  str.groups()[0]


print(name_from_path("/home/vadim/testword"))