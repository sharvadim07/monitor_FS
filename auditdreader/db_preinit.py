import subprocess
import os
import db
import logging
import datetime
import general
from stat import *


# TODO: make it more usable
class ImportantData(object):
    def __init__(self, st):
        self.inode = st.st_ino
        self.isdir = S_ISDIR(st.st_mode)
        self.lastChangeData = datetime.datetime.fromtimestamp(st.st_ctime)


def proceed_user(userid):
    # TODO: add database exception
    user = db.User.get_or_none(uid=userid)
    if user is None:
        db.User.get_or_create(uid=userid, defaults={'username': general.uid_to_usr_str(userid)})


def proceed_directory(entity):
    # TODO: add database exception
    proceed_user(entity['owner'])
    user = db.User.get_or_none(uid=entity['owner'])
    upper_parent = db.Directory.get_or_none(name=general.name_from_path(entity['directory']))
    db.Directory.get_or_create(owner=user, name=general.name_from_path(entity['path']),
                               inode=entity['info'].inode, parent=upper_parent,
                               time_update=entity['info'].lastChangeData, size=entity['size'])


def proceed_file(entity):
    # TODO: add database exception
    proceed_user(entity['owner'])
    user = db.User.get_or_none(uid=entity['owner'])
    upper_parent = db.Directory.get_or_none(name=general.name_from_path(entity['directory']))
    db.File.get_or_create(owner=user, name=general.name_from_path(entity['path']), inode=entity['info'].inode,
                          parent_id=upper_parent, time_update=entity['info'].lastChangeData, size=entity['size'])


def db_init():
    # TODO: add exceptions
    # TODO: add manual folder setting
    # there must be a path to the folder instead placeholder
    p = subprocess.Popen(["du", "/*placeholder*/", "-ab"], stdout=subprocess.PIPE, stderr=None)
    out = p.communicate()[0]
    out = out.decode("utf-8")
    data_grid = []
    for s in (out.split("\n")):
        if s != '':
            s = s.split("\t")
            temp_dict = {'size': s[0], 'path': s[1], 'info': ImportantData(os.stat(s[1])),
                         'owner': os.stat(s[1]).st_uid, 'directory': os.path.dirname(os.path.realpath(s[1]))}
            data_grid.append(temp_dict)
    data_grid.reverse()
    for temp in data_grid:
        if temp['info'].isdir:
            proceed_directory(temp)
    for temp in data_grid:
        if not temp['info'].isdir:
            proceed_file(temp)
        else:
            logging.warning("Unexpected file type!")

