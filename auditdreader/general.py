import subprocess
import re
import os, sys
from stat import *
import datetime


def uid_to_usr_str(uid):
    id_util_string = str(subprocess.check_output(['id', str(uid)]))
    if id_util_string:
        # uid = 1000(student)
        user_id_str = re.search(r'.*uid=[0-9]+[(]?(\w+)[)]?', id_util_string)
        if user_id_str:
            return user_id_str.groups()[0]
        else:
            return None

def name_from_path(path):
    str = re.search(r'[/](\w+)$', path)
    if str:
        return str.groups()[0]
    else:
        return  None


def parent_path_from_path(path):
    str = re.match(r'(.*)[/]\w+$', path)
    if str:
        return str.groups()[0]
    else:
        return  None

# This function takes the name of a file, and returns a
# 5-member tuple with the following contents:
# uid, inode , isdir, size, date of modify
def get_file_info(path):
    st = os.stat(path)
    return (st.st_uid, st.st_ino, S_ISDIR(st.st_mode), st.st_size,  datetime.datetime.fromtimestamp(st.st_mtime))

def get_file_path(event):
    if event.file_name[0] == '/':
        return  event.file_name
    elif event.file_name[0] == '.':
        return event.dir_path + name_from_path(event.file_name)
    else:
        return event.dir_path + event.file_name


