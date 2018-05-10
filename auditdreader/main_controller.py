import logging
import optparse
import time
import multiprocessing
import auditd_reader
import db
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


def add_fs_event_to_db(event):
    # TODO : Need add exception handler
    db.create_tables()

    user, user_created = db.User.get_or_create(
        uid = event.uid
    )
    if not user_created:
        user.username = event.uid_str


    directory = db.Directory.get_or_none(
        inode = event.dir_inode
    )
    if not directory:
            directory = db.Directory.create(inode = event.dir_inode)
            # 5-member tuple with the following contents:
            # uid, inode , isdir, size, date of modify
            dir_info = general.get_file_info(event.dir_path)
            if dir_info[1] != event.dir_inode:
                logging.warning("Directory path " + dir_info[1] + \
                                " is not match with dir inode " + event.file_inode)
            dir_owner, dir_owner_created = db.User.get_or_create(
                uid=dir_info[0]
            )
            directory.owner = dir_owner
            name = general.name_from_path(event.dir_path)
            if not name:
                logging.warning("Directory name will not set, dir inode:" + event.dir_inode)
                return -1
            directory.name = name
            # 5-member tuple with the following contents:
            # uid, inode , isdir, size, date of modify
            parent_info = general.get_file_info(general.parent_path_from_path(event.dir_path))
            parent_directory = db.Directory.get_or_none(
                inode = parent_info[1]
            )
            if parent_directory:
                directory.parent = parent_directory


    if event.evtype.type != "delete":
        # 5-member tuple with the following contents:
        # uid, inode , isdir, size, date of modify
        info_of_file_or_dir = general.get_file_info(general.get_file_path(event))
        if info_of_file_or_dir[1] != event.file_inode:
            logging.warning("File path " + general.get_file_path(event) + \
                            " is not match with file inode " + event.file_inode)
        if not info_of_file_or_dir[2]: # If is a file
            # TODO : add function for create a file
          pass
        else: # If is a directory
            # TODO : add function for create a directory
    else:
        dir = db.Directory.get_or_none(
            inode = event.file_inode
        )
        if dir:
            dir.delete_instance()
        else:
            file = db.File.get_or_none(
                inode =  event.file_inode
            )
            if file:
                file.delete_instance()


#worker(queue_fs_events)
add_fs_event_to_db()

db.database.close()