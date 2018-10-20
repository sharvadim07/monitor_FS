import subprocess
import re
import os, sys
from stat import *
import datetime


def uid_to_usr_str(uid):
    # id_util_string = str(subprocess.check_output(['id', str(uid)]))
    # if id_util_string:
    #     # uid = 1000(student)
    #     user_id_str = re.search(r'.*uid=[0-9]+[(]?(\w+)[)]?', id_util_string)
    #     if user_id_str:
    #         return user_id_str.groups()[0]
    #     else:
    #         return None
    # Checking by /etc/passwd
    try:
        user_file = open('/etc/passwd', 'r')
        userlines = user_file.readlines()
        user_file.close()
        for line in userlines:
            str = re.search(r"^[^:]*:[^:]*:%s:" % uid, line)
            if str:
                break
        usr_name = re.search(r"^[^:]+", str.group()).group()
        return usr_name
    except IOError as e_status:
        raise e_status

def name_from_path(path):
    str = re.search(r'[/](\w+)[/]?$', path)
    if str:
        return str.groups()[0]
    else:
        return  None


def parent_path_from_path(path):
    str = re.match(r'(.*)[/]\w+[/]?$', path)
    if str:
        return str.groups()[0]
    else:
        return  None

class FileInfo(object):
    def __init__(self, st):
        self.uid = st.st_uid
        self.inode = st.st_ino
        self.isdir = S_ISDIR(st.st_mode)
        self.size = st.st_size
        self.date_change = datetime.datetime.fromtimestamp(st.st_ctime)

def get_file_info(path):
    """
    # This function takes the name of a file, and returns a
    5-member FileInfo object with the following attributes:
    uid, inode , isdir, size, date of change
    :param path: Path to file in file system
    :return: Object of FileInfo class
    """
    return FileInfo(os.stat(path))






