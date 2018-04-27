import time
import multiprocessing
import logging
import fs_event
import re

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


class AuditReaderProcess(multiprocessing.Process):
    """
    Audit Reader Process parse auditd log lines and generate new FSEvent objects.
    Performed as a separated process
    Arguments:
        auditd_name_file -- path and name to auditd log file
        output_q -- queue (multiprocessing.JoinableQueue()) for sending FSEvents Objects
    Methods:
        run -- run this
    """

    def __init__(self, auditd_name_file, output_q):
        multiprocessing.Process.__init__(self)
        self.auditd_name_file = auditd_name_file
        self.output_q = output_q
        self.events_dict = dict()

    def run(self):
        try:
            # create queue
            queue = multiprocessing.JoinableQueue()
            # create reader process
            proc_reader = ReaderProcess(self.auditd_name_file, queue)
            proc_reader.daemon = True
            # start reader deamon
            proc_reader.start()

            # list of auditd log lines (strings)
            audit_lines = queue.get()
            # if file not empty then start processing it
            if len(audit_lines) > 0:
                # parse first lines which readed
                self.parse_audit_lines(audit_lines)
                queue.task_done()
                # clean readed lines
                audit_lines = []
                # while reader deamon working we add NEW lines to list audit_lines and parse its
                while proc_reader.is_alive():
                    if queue.empty():
                        if len(audit_lines) > 0:
                            self.parse_audit_lines(audit_lines)
                            # Send new events to controller
                            for ev in self.events_dict:
                                self.output_q.put(ev)
                            # Clear dictionary
                            self.events_dict = dict()
                            audit_lines = []
                        time.sleep(5)
                    else:
                        line = queue.get()
                        audit_lines.append(line)
            else:
                logging.error("Audit file is empty!")
                proc_reader.terminate()
                raise IOError
        except (IOError, ChildProcessError) as e_status:
            logging.error(e_status)
            raise e_status

    def parse_audit_line(self,line):

        """
        Parsing one current line from auditd log. Also add and edit new FSEvents
        :param line: current line for parsing
        :return: return -1 if error while parsing
        """
        # All lines in auditd log consist strings of this REGEXP
        try:
            type_and_id = re.search(r'type=(\w+).+audit[(]?([0-9.:]+)[:]?', line)
            if type_and_id and type_and_id.groups()[0] in ("SYSCALL", "CWD", "PATH"):
                event = self.events_dict.get(type_and_id.groups()[1])
                if not event:  # If event is not exist then create it
                    if type_and_id.groups()[0] == "SYSCALL":  # parsing SYSCALL line
                        num_items = re.search(r' items=([0-9]{1,5}) ', line)
                        if num_items and num_items.groups()[0] != "0":
                            # add events
                            logging.debug("Add syscall " + type_and_id.groups()[1] + " to events dictionary")
                            event = fs_event.FSEvent(type_and_id.groups()[1])
                            self.events_dict[type_and_id.groups()[1]] = event
                            # Set num items
                            event.cur_items = int(num_items.groups()[0])
                            # Set event type
                            event.parse_syscall_num(line)
                            # Set user id
                            event.parse_uid(line)
                        else:
                            # logging.debug("In line\n" + line + "\n SYSCALL not for files or directory. Items = 0")
                            return -2
                    elif type_and_id.groups()[0] in ("CWD", "PATH"):
                        logging.warning("In line\n" + line + "\n not expected CWD or PATH type")
                        return -1
                else:  # If event is exist then modify it
                    if type_and_id.groups()[0] == "SYSCALL":
                        logging.warning("In line\n" + line + "\n not expected SYSCALL type")
                        return -1
                    elif type_and_id.groups()[0] == "CWD":  # parsing CWD line
                        # Set event directory path
                        event.parse_cwd(line)
                    elif type_and_id.groups()[0] == "PATH":  # parsing PATH line
                        if event.dir_path:
                            if event.evtype.type == "rename":
                                # Create additional event for rename or move syscalls
                                if event.parse_path_line(line, True):
                                    self.events_dict[event.ad_event.id] = event.ad_event
                            else:
                                # Set file name or directory name
                                event.parse_path_line(line)
                        else:
                            logging.warning("CWD not set, path may be incorrect!")
                            return -1
        except:
            logging.error("Error while parsing audit line")
            return -1

    def parse_audit_lines(self, audit_lines):
        """
        Parse a few auditd log lines
        :param audit_lines: list of of few auditd lines
        :param ptr_read_line: a pointer in list audit_lines where to start parsing
        :return:
        """
        #ptr_read_line_after_parse = ptr_read_line
        for cur_line in audit_lines:
            self.parse_audit_line(cur_line)
        #     ptr_read_line_after_parse += 1
        # return ptr_read_line_after_parse


