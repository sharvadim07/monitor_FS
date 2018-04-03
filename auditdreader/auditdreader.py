import optparse
import time
import multiprocessing
import asyncio
import sys

p = optparse.OptionParser()
p.add_option("-i", action="store", type="string", dest="infile", default="/var/log/audit/audit1.log")

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
    def __init__(self,id,file_name,dir_path,uid,type,time,volume_info):
        self.id=id
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
    @property
    def time(self):
        return self.__time
    @property
    def volume_info(self):
        return self.__volume_info
    @id.setter
    def id(self, id):
        if isinstance(id,str):
            self.__id = id
        else:
            print("Incorrect type for id attribute!")
            self.set_create()  # default
    @file_name.setter
    def file_name(self, file_name):
        if isinstance(file_name, str):
            self.__file_name = file_name
        else:
            print("Incorrect type for file_name attribute!")
            self.set_create()  # default


class ListFSEvent():
    def __init__(self,fs_event):
        self.size = 0



def parse_audit_line(line):
    pass

def parse_audit_lines(audit_lines,ptr_read_line):
    ptr_read_line_after_parse = ptr_read_line
    for cur_line in audit_lines[ptr_read_line,]:
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


