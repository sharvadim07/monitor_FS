import logging
import optparse
import time
import multiprocessing
import auditd_reader
import db
import os
import general

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


def add_fs_event_to_db(event=None):
    db.create_tables()

    user, user_created = db.User.get_or_create(
        uid = event.uid
    )
    # TODO : build this function
    directory, directory_created = db.Directory.get_or_create(
        path = event.dir_path,
        inode = event.dir_inode
    )
    st = get_directory_info(event)
    dir_owner, dir_owner_created = db.User.get_or_create(
        uid = st.uid
    )
    if not dir_owner_created:
        username = general.uid_to_usr_str(dir_owner.uid)
        if username:
            dir_owner.username = username
        else:
            logging.warning("Uid to username conflict!")
    directory.owner = dir_owner
    if directory_created:
        directory.size =


# This function takes the name of a file, and returns a
# 10-member tuple with the following contents:
#mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime
def get_directory_info(event):
    st = os.stat(event.dir_path)
    if st.st_ino == event.dir_inode:
        return st
    else:
        logging.warning("Dir path " + event.dir_path + " not match with inode "  + event.dir_inode)


#worker(queue_fs_events)
add_fs_event_to_db()

db.database.close()