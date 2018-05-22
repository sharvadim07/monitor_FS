import logging
import optparse
import time
import multiprocessing
import auditd_reader
import db
import db_control

# parse programm options
p = optparse.OptionParser()
p.add_option("-i", action="store", type="string", dest="infile", default="/var/log/audit/audit.log")
opts, args = p.parse_args()
logging.basicConfig(filename="auditreader.log", level=logging.WARNING)

# get auditd file path and name
auditd_name_file = opts.infile

# dict of FSEvents key is event ID


queue_fs_events = multiprocessing.Queue()
# create reader process
proc_au_reader = auditd_reader.AuditReaderProcess(auditd_name_file, queue_fs_events)
proc_au_reader.daemon = True

def add_events_to_db( events_list ):
    for event in events_list:
        if event.id[-2:] == ".1": # If it is ad_event then pass
            continue
        try:
            db_control.add_fs_event_to_db(event)
        except FileNotFoundError as err:
            logging.warning(err + ' in event - ' + event.id)

def worker ( queue_fs_events ):
    # start reader deamon
    proc_au_reader.start()
    events_list = []
    while True:
        if not queue_fs_events.empty():
            events_list.append(queue_fs_events.get())
            # TODO : Add event to database
        elif len(events_list):
                add_events_to_db(events_list)
                events_list.clear()
        else:
            time.sleep(2)
            # TODO : Work with data base and scanning

db.create_tables()
worker(queue_fs_events)
db.database.close()