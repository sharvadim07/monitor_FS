import optparse
import time
import multiprocessing
import re
import asyncio
import sys

p = optparse.OptionParser()
p.add_option("-i", action="store", type="string", dest="infile", default="/var/log/audit/audit.log")

opts, args = p.parse_args()
auditd_name_file = opts.infile


class ReaderProcess(multiprocessing.Process):
    def __init__(self, auditd_name_file, output_q):
        multiprocessing.Process.__init__(self)
        self.auditd_name_file = auditd_name_file
        self.output_q = output_q
    def run(self):
        try:
            audit_file = open(self.auditd_name_file, 'r');
            audit_lines = audit_file.readlines()
            self.output_q.put(audit_lines)
            self.output_q.join()
            while True:
                line = audit_file.readline()
                if line:
                    self.output_q.put(line)
                else:
                    time.sleep(1)
        except (IOError,ChildProcessError) as e_status:
            return e_status

class EventType(object):
    def __init__(self,type):
        self.type=type
    def set_create(self):
        self.__type = "create"
    def set_change(self):
        self.__type = "change"
    def set_delete(self):
        self.__type = "delete"
    @property
    def type(self):
        return self.__type
    @type.setter
    def type(self,type):
        if type in ( "create" , "change" , "delete"):
            self.__type = type
        else:
            print("Set default type - create.")
            self.set_create()  # default

class FSEvent(object):
    num_fs_events = 0
    def __init__(self,id):
        self.__id=id
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
    def dir_path(self):
        return self.__dir_path
    @property
    def uid(self):
        return self.__uid
    @property
    def type(self):
        return self.__type
    # @property
    # def time(self):
    #     return self.__time
    # @property
    # def volume_info(self):
    #     return self.__volume_info

    @id.setter
    def id(self, id):
        if isinstance(id,str):
            self.__id = id
        else:
            print("Incorrect type for id attribute!")
            raise TypeError

    @file_name.setter
    def file_name(self, file_name):
        if isinstance(file_name, str):
            self.__file_name = file_name
        else:
            print("Incorrect type for file_name attribute!")
            raise TypeError

    @dir_path.setter
    def dir_path(self, dir_path):
        if isinstance(dir_path, str):
            self.__dir_path = dir_path
        else:
            print("Incorrect type for dir_path attribute!")
            raise TypeError

    @uid.setter
    def uid(self, uid):
        if isinstance(uid, str):
            self.__uid = uid
        else:
            print("Incorrect type for uid attribute!")
            raise TypeError

    @type.setter
    def type(self, type):
        if isinstance(type, EventType):
            self.__type = type
        else:
            print("Incorrect type for type attribute!")
            raise TypeError

#dict of FSevents key is event ID
events_dict = dict()

def parse_audit_line(line):
    type_and_id=re.search(r'type=(\w+).+audit[(]?([0-9.:]+)[:]?',line)
    if type_and_id and type_and_id.groups()[0] in [ "SYSCALL" , "CWD" , "PATH" ]:
        if type_and_id.groups()[0] == "SYSCALL":
            if not type_and_id.groups()[1] in events_dict:
                event = FSEvent(type_and_id.groups()[1])
                events_dict[type_and_id.groups()[1]] = event
                
        else type_and_id.groups()[0] == "CWD"




def parse_audit_lines(audit_lines,ptr_read_line):
    ptr_read_line_after_parse = ptr_read_line
    for cur_line in audit_lines[ptr_read_line:]:
        parse_audit_line(cur_line)
        ptr_read_line_after_parse += 1
    return ptr_read_line_after_parse


queue = multiprocessing.JoinableQueue()
proc_reader = ReaderProcess(auditd_name_file, queue)
proc_reader.daemon = True
proc_reader.start()

audit_lines = queue.get()
#for line in audit_lines:
if len(audit_lines) > 0:
    ptr_read_line = 0
    ptr_read_line = parse_audit_lines(audit_lines,ptr_read_line)
    queue.task_done()
    while proc_reader.is_alive():
        if queue.empty():
            if ptr_read_line < len(audit_lines):
                ptr_read_line = parse_audit_lines(audit_lines,ptr_read_line)
            #for debug
            #print("sleep 5 sec")
            #sys.stdout.flush()
            time.sleep(5)
        else:
            line = queue.get()
            audit_lines.append(line)

            # for debug
            #print("new line:", line)
            #sys.stdout.flush()
else:
    print("Audit file is empty!")
    proc_reader.terminate()


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