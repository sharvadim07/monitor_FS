import logging
import re
import subprocess

class FSEvent(object):
    """
    File System Event
    variables:
    1 - number of file system events
    properties:
    id -- string of event ID
    file_name -- file name
    dir_path -- directory path
    type -- event type (object of class EventType)
    uid -- user id
    uid_str -- user name (string)
    type -- time of changes
    volume_info -- volume of data in Kbytes
    """
    num_fs_events = 0

    def __init__(self, id):
        self.__id = id
        self.__type = EventType()
        # self.__file_name = file_name
        # self.__dir_path = dir_path
        # self.__uid = uid
        # self.__type = EventType(type)
        # self.__time = time
        # self.__volume_info = volume_info  # In bytes
        FSEvent.num_fs_events += 1

    def __del__(self):
        FSEvent.num_fs_events -= 1

    @property
    def id(self):
        return self.__id

    @property
    def file_name(self):
        return self.__file_name

    @property
    def file_inode(self):
        return self.__file_inode

    @property
    def dir_path(self):
        return self.__dir_path

    @property
    def dir_inode(self):
        return self.__dir_inode

    @property
    def uid(self):
        return self.__uid

    @property
    def uid_str(self):
        return self.__uid_str

    @property
    def evtype(self):
        return self.__type

    # PThis property for correct parsing all syscall items
    @property
    def cur_items(self):
        return self.__cur_items

    @property
    def ad_event(self):
        return self.__ad_event

    # @property
    # def time(self):
    #     return self.__time
    # @property
    # def volume_info(self):
    #     return self.__volume_info

    @id.setter
    def id(self, id):
        if isinstance(id, str):
            self.__id = id
        else:
            logging.error("Incorrect type for id attribute!")
            raise TypeError

    @file_name.setter
    def file_name(self, file_name):
        if isinstance(file_name, str):
            self.__file_name = file_name
        else:
            logging.error("Incorrect type for file_name attribute!")
            raise TypeError

    @file_inode.setter
    def file_inode(self, file_inode):
        if isinstance(file_inode, int):
            self.__file_inode = file_inode
        else:
            logging.error("Incorrect type for file_inode attribute!")
            raise TypeError

    @dir_path.setter
    def dir_path(self, dir_path):
        if isinstance(dir_path, str):
            self.__dir_path = dir_path
        else:
            logging.error("Incorrect type for dir_path attribute!")
            raise TypeError

    @dir_inode.setter
    def dir_inode(self, dir_inode):
        if isinstance(dir_inode, int):
            self.__dir_inode = dir_inode
        else:
            logging.error("Incorrect type for dir_inode attribute!")
            raise TypeError

    @uid.setter
    def uid(self, uid):
        if isinstance(uid, int):
            self.__uid = int(uid)
            # Read result id util
            try:
                id_util_string = str(subprocess.check_output(['id', str(uid)]))
                if id_util_string:
                    # uid = 1000(student)
                    user_id_str = re.search(r'.*uid=[0-9]+[(]?(\w+)[)]?', id_util_string)
                    if user_id_str:
                        self.uid_str = user_id_str.groups()[0]
                    else:
                        logging.warning(self.id + "not set uid_str")
            except TypeError as e:
                logging.error("Error in conversion uid to uid_str")
                raise e

        else:
            logging.error("Incorrect type for uid attribute!")
            raise TypeError

    @uid_str.setter
    def uid_str(self, uid_str):
        if isinstance(uid_str, str):
            self.__uid_str = uid_str
        else:
            logging.warning("Incorrect type for uid_str attribute!")
            raise TypeError

    @evtype.setter
    def evtype(self, type):
        if isinstance(type, str):
            self.__type.type = type
        else:
            logging.warning("Incorrect type for type attribute!")
            raise TypeError

    @cur_items.setter
    def cur_items(self, cur_items):
        if isinstance(cur_items, int):
            self.__cur_items = cur_items
        else:
            logging.warning("Incorrect type for cur_items attribute!")
            raise TypeError

    @ad_event.setter
    def ad_event(self, ad_event):
        if isinstance(ad_event, FSEvent):
            self.__ad_event = ad_event
        else:
            logging.warning("Incorrect type for ad_event attribute!")
            raise TypeError


    def set_dir_path_and_inode (self, name, inode):
        if name[0] == '.':
            self.dir_path += name[1:]
        else:
            self.dir_path = name
        self.dir_inode = int(inode)

    def set_file_name_and_inode (self, name, inode):
        if name[0] == '.':
            self.file_name += name[1:]
        else:
            self.file_name = name
        self.file_inode = int(inode)

    def set_nametype(self, name_type):
        # Set event type
        if name_type == "CREATE":
            self.evtype.set_create()
        elif name_type == "DELETE":
            self.evtype.set_delete()
        # elif name_type.groups()[0] == "NORMAL":
        else:
            self.evtype.set_change()

    def parse_path_line(self, line, move_flag = False):
        # Set file name or directory name
        path_line = re.search(r' item=([0-9]{1,3}).*name=["]?([^"]+)["]?.*inode=(\w+).*nametype=(\w+)', line)
        #path_line = re.search(r' item=([0-9]{1,3}).*name=([^"]+).*inode=(\w+).*nametype=(\w+)', line)
        if path_line:
            if not move_flag:
                if  int(path_line.groups()[0]) == 0:  # parent directory path (first item in syscall)
                    self.set_dir_path_and_inode(path_line.groups()[1], path_line.groups()[2])
                else:  # file path
                    self.set_file_name_and_inode(path_line.groups()[1], path_line.groups()[2])
                    self.set_nametype(path_line.groups()[3])
            else:
                # TODO : fix it
                if int(path_line.groups()[0]) == 0:
                    self.set_dir_path_and_inode(path_line.groups()[1], path_line.groups()[2])
                    self.ad_event = FSEvent(self.id + '.1')
                    self.ad_event.ad_event = self
                    return self.ad_event
                elif int(path_line.groups()[0]) == 1:
                    self.ad_event.set_dir_path_and_inode(path_line.groups()[1], path_line.groups()[2])
                elif int(path_line.groups()[0]) == self.cur_items-2:
                    self.set_file_name_and_inode(path_line.groups()[1], path_line.groups()[2])
                    #self.set_nametype(path_line.groups()[3])
                elif int(path_line.groups()[0]) == self.cur_items-1:
                    self.ad_event.set_file_name_and_inode(path_line.groups()[1], path_line.groups()[2])
                    #self.ad_event.set_nametype(path_line.groups()[3])
                    self.ad_event.evtype.set_create()
                    self.evtype.set_delete()
        else:
            logging.warning(self.id + "not set path or filename")

    def parse_syscall_num(self, line):
        # Set event type
        syscall_num = re.search(r' syscall=([0-9]{1,5}) ', line)
        if syscall_num:
            self.evtype = syscall_num.groups()[0]
        else:
            logging.warning(self.id + "not set type")

    def parse_uid(self,line):
        # Set user id
        user_id = re.search(r' uid=(\w+) ', line)
        if user_id:
            self.uid = int(user_id.groups()[0])
        else:
            logging.warning(self.id + "not set uid")

    def parse_cwd(self, line):
        # Set event directory path
        cwd = re.search(r' cwd=["]?([^"]+)["]?', line)
        if cwd:
            self.dir_path = cwd.groups()[0]
        else:
            logging.warning(self.id + "not set cwd path")


class EventType(object):
    """
    Event Type
    properties:
        type -- type in string format. use setter of change value
    """

    def __init__(self, type = "change"):
        self.type = type

    def set_create(self):
        self.__type = "create"

    def set_change(self):
        self.__type = "change"

    def set_delete(self):
        self.__type = "delete"

    def set_rename(self):
        self.__type = "rename"

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, type):
        if type in ("create", "change", "delete", "rename"):
            self.__type = type
        elif type in ("5","8","9","39"):
            self.set_create()
        elif type in ("10","40","301"):
            self.set_delete()
        elif type in ("38"):
            self.set_rename()
        else:
            logging.warning("Set default type - change.")
            self.set_change()  # default








