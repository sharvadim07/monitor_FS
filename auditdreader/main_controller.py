import logging
import optparse
import time
import multiprocessing
import auditd_reader

# parse programm options
p = optparse.OptionParser()
p.add_option("-i", action="store", type="string", dest="infile", default="/var/log/audit/audit.log")
opts, args = p.parse_args()
logging.basicConfig(filename="auditdreader.log", level=logging.DEBUG)

##MAIN

# get auditd file path and name
auditd_name_file = opts.infile

# dict of FSEvents key is event ID


queue_fs_events = multiprocessing.Queue()
# create reader process
proc_au_reader = auditd_reader.AuditReaderProcess(auditd_name_file, queue_fs_events)
proc_au_reader.daemon = True


def worker (queue_fs_events):
    # start reader deamon
    proc_au_reader.start()
    while True:
        if not queue_fs_events.empty():
            event = queue_fs_events.get()
            # TODO : Add event to database
        else:
            time.sleep(20)
            # TODO : Work with data base and scanning


worker(queue_fs_events)