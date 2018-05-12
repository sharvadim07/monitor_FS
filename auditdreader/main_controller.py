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

def db_create_or_get_ins_file_or_dir_from_event(db_model, event_inode, event_path, event_parent = None):
    instance_of_model_file_dir = db_model.get_or_none(
        inode=event_inode
    )
    create_flag = False
    if not instance_of_model_file_dir:
        create_flag = True
        instance_of_model_file_dir = db_model.create(inode=event_inode)
        # 5-member tuple with the following contents:
        # uid, inode , isdir, size, date of modify
        dir_info = general.get_file_info(event_path)
        if dir_info[1] != event_inode:
            logging.warning("Path " + dir_info[1] + \
                            " is not match with inode " + event_inode)
        # Set owner
        instance_of_model_file_dir.owner = db_get_or_create_user(dir_info[0], general.uid_to_usr_str(dir_info[0]))
        # Set name
        name = general.name_from_path(event_path)
        if not name:
            logging.warning("Name will not set, inode:" + event_inode)
            return -1
        instance_of_model_file_dir.name = name
        # Set parent
        if not event_parent:
            # 5-member tuple with the following contents:
            # uid, inode , isdir, size, date of modify
            parent_info = general.get_file_info(general.parent_path_from_path(event_path))
            parent_directory = db.Directory.get_or_none(
                inode=parent_info[1]
            )
            if parent_directory:
                instance_of_model_file_dir.parent = parent_directory
        else:
            instance_of_model_file_dir.parent = event_parent


    return (instance_of_model_file_dir, create_flag)

def db_get_or_create_user(uid,uid_str):
    user, user_created = db.User.get_or_create(
        uid=uid,
        defaults={'username': uid_str}
    )
    return user


def add_fs_event_to_db(event):
    # TODO : Need add exception handler
    db.create_tables()

    user = db_get_or_create_user(event.uid, event.uid_str)
    parent_dir = db_create_or_get_ins_file_or_dir_from_event(db.Directory, event.dir_inode, event.dir_path)

    if event.evtype.type != "delete":
        # 5-member tuple with the following contents:
        # uid, inode , isdir, size, date of modify
        info_of_file_or_dir = general.get_file_info(general.get_file_path(event))
        if info_of_file_or_dir[1] != event.file_inode:
            logging.warning("File or directory path name " + general.get_file_path(event) + \
                            " is not match with inode " + event.file_inode)
        if not info_of_file_or_dir[2]: # If is a file
            # Function to create a file
            file = db_create_or_get_ins_file_or_dir_from_event(db.File, event.file_inode, \
                                                              general.get_file_path(event), parent_dir)
            file.size = info_of_file_or_dir[3]
            file.time_update = info_of_file_or_dir[4]
        else: # If is a directory
            # Function to create a directory
            dir = db_create_or_get_ins_file_or_dir_from_event(db.Directory,event.file_inode, \
                                                              general.get_file_path(event), parent_dir)
            dir.size = info_of_file_or_dir[3]
            dir.time_update = info_of_file_or_dir[4]

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