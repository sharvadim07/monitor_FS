import optparse
import time
import multiprocessing
import re
import logging
import subprocess
import asyncio
import sys

# parse programm options
p = optparse.OptionParser()
p.add_option("-i", action="store", type="string", dest="infile", default="/var/log/audit/audit.log")
opts, args = p.parse_args()
logging.basicConfig(filename="auditdreader.log", level=logging.DEBUG)

class ReaderProcess(multiprocessing.Process):
    """
    Reader Process of auditd logging file. Performed as a separated process
    Arguments:
        auditd_name_file -- path and name to auditd log file
        output_q -- queue (multiprocessing.JoinableQueue()) for sending read lines to the parent process
    Methods:
        run -- run the read auditd log file
    """

    def __init__(self, auditd_name_file, output_q):
        multiprocessing.Process.__init__(self)
        self.auditd_name_file = auditd_name_file
        self.output_q = output_q

    def run(self):
        try:
            audit_file = open(self.auditd_name_file, 'r')
            audit_lines = audit_file.readlines()
            self.output_q.put(audit_lines)
            self.output_q.join()
            while True:
                line = audit_file.readline()
                if line:
                    self.output_q.put(line)
                else:
                    time.sleep(1)
        except (IOError, ChildProcessError) as e_status:
            logging.error(e_status)
            raise e_status


class EventType(object):
    """
    Event Type
    properties:
        type -- type in string format. use setter of change value
    """

    def __init__(self, type):
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
        if isinstance(type, EventType):
            self.__type = type
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
                    self.set_nametype(path_line.groups()[3])
                elif int(path_line.groups()[0]) == self.cur_items-1:
                    self.ad_event.set_file_name_and_inode(path_line.groups()[1], path_line.groups()[2])
                    self.ad_event.set_nametype(path_line.groups()[3])
                    self.ad_event.evtype.set_create()
                    self.evtype.set_delete()
        else:
            logging.warning(self.id + "not set path or filename")

    def parse_syscall_num(self, line):
        # Set event type
        syscall_num = re.search(r' syscall=([0-9]{1,5}) ', line)
        if syscall_num:
            self.evtype = EventType(syscall_num.groups()[0])
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




def parse_audit_line(line):

    """
    Parsing one current line from auditd log. Also add and edit new FSEvents
    :param line: current line for parsing
    :return: return -1 if error while parsing
    """
    # maybe this dict should be as parameter
    global events_dict
    # All lines in auditd log consist strings of this REGEXP
    try:
        type_and_id = re.search(r'type=(\w+).+audit[(]?([0-9.:]+)[:]?', line)
        if type_and_id and type_and_id.groups()[0] in ("SYSCALL", "CWD", "PATH"):
            event = events_dict.get(type_and_id.groups()[1])
            if not event: # If event is not exist then create it
                if type_and_id.groups()[0] == "SYSCALL": # parsing SYSCALL line
                    num_items = re.search(r' items=([0-9]{1,5}) ', line)
                    if num_items and num_items.groups()[0] != "0":
                        # add events
                        logging.debug("Add syscall " + type_and_id.groups()[1] + " to events dictionary")
                        event = FSEvent(type_and_id.groups()[1])
                        events_dict[type_and_id.groups()[1]] = event
                        # Set num items
                        event.cur_items=int(num_items.groups()[0])
                        # Set event type
                        event.parse_syscall_num(line)
                        # Set user id
                        event.parse_uid(line)
                    else:
                        #logging.debug("In line\n" + line + "\n SYSCALL not for files or directory. Items = 0")
                        return -2
                elif type_and_id.groups()[0] in ("CWD", "PATH"):
                    logging.warning("In line\n"+line+"\n not expected CWD or PATH type")
                    return -1
            else: # If event is exist then modify it
                if type_and_id.groups()[0] == "SYSCALL":
                    logging.warning("In line\n" + line + "\n not expected SYSCALL type")
                    return -1
                elif type_and_id.groups()[0] == "CWD":  # parsing CWD line
                    # Set event directory path
                    event.parse_cwd(line)
                elif type_and_id.groups()[0] == "PATH":   # parsing PATH line
                    if event.dir_path:
                        if event.evtype.type == "rename":
                            # Create additional event for rename or move syscalls
                            if event.parse_path_line(line, True):
                                events_dict[event.ad_event.id] = event.ad_event
                        else:
                            # Set file name or directory name
                            event.parse_path_line(line)
                    else:
                        logging.warning("CWD not set, path may be incorrect!")
                        return -1
    except:
        logging.error("Error while parsing audit line")
        return -1


def parse_audit_lines(audit_lines, ptr_read_line):
    """
    Parse a few auditd log lines
    :param audit_lines: list of of few auditd lines
    :param ptr_read_line: a pointer in list audit_lines where to start parsing
    :return:
    """
    ptr_read_line_after_parse = ptr_read_line
    for cur_line in audit_lines[ptr_read_line:]:
        parse_audit_line(cur_line)
        ptr_read_line_after_parse += 1
    return ptr_read_line_after_parse


###MAIN

# get auditd file path and name
auditd_name_file = opts.infile

# dict of FSevents key is event ID
events_dict = dict()

# create queue
queue = multiprocessing.JoinableQueue()
# create reader process
proc_reader = ReaderProcess(auditd_name_file, queue)
proc_reader.daemon = True
# start reader deamon
proc_reader.start()

# list of auditd log lines (strings)
audit_lines = queue.get()

# if file not empty then start processing it
if len(audit_lines) > 0:
    ptr_read_line = 0
    # parse first lines which readed
    ptr_read_line = parse_audit_lines(audit_lines, ptr_read_line)
    queue.task_done()
    # while reader deamon working we add NEW lines to list audit_lines and parse its
    while proc_reader.is_alive():
        if queue.empty():
            if ptr_read_line < len(audit_lines):
                ptr_read_line = parse_audit_lines(audit_lines, ptr_read_line)
            # for debug
            # print("sleep 5 sec")
            # sys.stdout.flush()
            time.sleep(5)
        else:
            line = queue.get()
            audit_lines.append(line)
            # for debug
            # print("new line:", line)
            # sys.stdout.flush()
else:
    logging.error("Audit file is empty!")
    proc_reader.terminate()
    raise IOError

# class ListFSEvent():
#     def __init__(self,fs_event):
#         if isinstance(fs_event,FSEvent)
#             self.fs_event = self.fs_event.append(fs_event)
#             self.index = len(self.fs_event)
#             self.size = len(self.fs_event)
#         else:
#             print("Incorrect type for file_name attribute!")
#             raise TypeError
#
#     def add(self, fs_event):
#         if isinstance(fs_event,FSEvent)
#             self.fs_event = self.fs_event.append(fs_event)
#             self.index = len(self.fs_event)
#             self.size = len(self.fs_event)
#         else:
#             print("Incorrect type for file_name attribute!")
#             raise TypeError
#     def search(self,id):
#         for ev in self:
#             if(self.fs_event.id == id):
#                 return self.fs_event
#     def remove(self,id):
#         for ev in self:
#             if(ev.fs_event.id == id):
#                 self.remove(ev)
#
#
#     def __iter__(self):
#         return self.fs_event[self.index]
#
#     def __next__(self):
#         if self.index == self.size
#             raise StopIteration
#         self.index = self.index + 1
#         return self.fs_event[self.index]
