import db
import general
import logging

# test git

def get_file_path(event):
    if event.file_name[0] == '/':
        return  event.file_name
    elif event.file_name[0] == '.':
        return event.dir_path + general.name_from_path(event.file_name)
    else:
        return event.dir_path + "/" + event.file_name

# 5-member tuple with the following contents:
# uid, inode , isdir, size, date of change
def get_info_by_event(event = None, event_path = None, event_inode = None):
    try:
        if event_path == None:
            info_of_file_or_dir = general.get_file_info(get_file_path(event))
            if info_of_file_or_dir.inode != event.file_inode:
                raise FileNotFoundError
        else:
            info_of_file_or_dir = general.get_file_info(event_path)
            if event_inode and info_of_file_or_dir.inode != event_inode:
                raise FileNotFoundError
    except FileNotFoundError as e:
        # TODO: Do normal logging this warning
        logging.warning("File not exist or inode file in syscall not match with inode in file system.")
    return info_of_file_or_dir

def db_create_or_get_ins_file_or_dir_from_event( db_model, event_inode, event_path, event_parent = None, info = None ):
    instance_of_model_file_dir = db_model.get_or_none(
        inode=event_inode
    )
    create_flag = False
    if not instance_of_model_file_dir:
        create_flag = True
        # uid, inode , isdir, size, date of modify
        if info:
            info_of_file_or_dir = info
        else:
            info_of_file_or_dir = get_info_by_event(None, event_path, event_inode)
        # Create new instance
        instance_of_model_file_dir = db_model.create(inode=event_inode)
        # Set owner
        instance_of_model_file_dir.owner = db_get_or_create_user(info_of_file_or_dir.uid,
                                                                 general.uid_to_usr_str(info_of_file_or_dir.uid))
        # Set name
        name = general.name_from_path(event_path)
        if not name:
            logging.warning("Name will not set, inode:" + str(event_inode))
            return -1
        instance_of_model_file_dir.name = name
        # Set initial size 0
        instance_of_model_file_dir.size = info_of_file_or_dir.size
        # Set time update
        instance_of_model_file_dir.time_update = info_of_file_or_dir.date_change
        # Set parent
        if not event_parent:
            # uid, inode , isdir, size, date of modify
            parent_info = get_info_by_event(None, general.parent_path_from_path(event_path))
            parent_directory = db.Directory.get_or_none(
                inode=parent_info.inode
            )
            if parent_directory:
                instance_of_model_file_dir.parent = parent_directory
        else:
            instance_of_model_file_dir.parent = event_parent
        #instance_of_model_file_dir.save()
    return (instance_of_model_file_dir, create_flag)

def db_get_or_create_user( uid, uid_str ):
    user, user_created = db.User.get_or_create(
        uid=uid,
        defaults={'username': uid_str}
    )
    return user

def update_parent_size( instance, new_size, time_update ):
    # May be need method get of db
    if not instance.parent:
        return
    instance.parent.size += new_size
    instance.parent.time_update = time_update

    update_parent_size(instance.parent, new_size, time_update)

def update_file_parent_size( create_flag, file,size,time_update ):
    # Update all parents directory size
    if create_flag:
        update_parent_size(file, size, time_update)
    else:
        update_size = size - file.size
        if update_size != 0:
            update_parent_size(file, update_size, time_update)


def instance_file_dir_rename_or_move( db_model, old_event_inode, new_event_inode, event_path_to,
                                     parent_dir_to, time_update, info ):
    inst, create_flag = db_create_or_get_ins_file_or_dir_from_event(db_model, old_event_inode,
                                                                    event_path_to, parent_dir_to, info)
    if old_event_inode != new_event_inode:
        inst.inode = new_event_inode
    if not create_flag:
        inst.name = general.name_from_path(event_path_to)
        inst.parent = parent_dir_to
    inst.time_update = time_update

    return (inst, create_flag)



def update_instance_of_file_dir_model( event, move_flag ):


    """
    Updating or creating new instance (file, directory) in db affected by the event
    :param event: event
    :param move_flag: move or create/change/delete flag
    :return: return db instance (file or directory) or None if file does not exist at this moment
                and flag Is a directory or not
    """
    parent_dir = None
    info_of_file_or_dir = None

    if(move_flag):
        parent_dir, create_flag = db_create_or_get_ins_file_or_dir_from_event(db.Directory,
                                                                              event.ad_event.dir_inode, event.ad_event.dir_path)
        info_of_file_or_dir = get_info_by_event(event.ad_event, None)
    else:
        parent_dir, create_flag  = db_create_or_get_ins_file_or_dir_from_event(db.Directory,
                                                                               event.dir_inode, event.dir_path)
        info_of_file_or_dir = get_info_by_event(event, None)

    if info_of_file_or_dir == None:
        return None

    if not info_of_file_or_dir.isdir:  # If is a file
        if (move_flag):
            # Function to update a file
            file, create_flag = instance_file_dir_rename_or_move(db.File, event.file_inode, event.ad_event_inode,
                                                                 get_file_path(event.ad_event), parent_dir,
                                                                 info_of_file_or_dir.date_change, info_of_file_or_dir)
        else:
            # Function to create a file
            file, create_flag = db_create_or_get_ins_file_or_dir_from_event(db.File, event.file_inode,
                                                                            get_file_path(event),
                                                                            parent_dir,
                                                                            info_of_file_or_dir)
        # Update all parents directory size
        update_file_parent_size(create_flag, file, info_of_file_or_dir.size, info_of_file_or_dir.date_change)
        # Save changes in db for parent directory
        parent_dir.save()
        file.size = info_of_file_or_dir.size
        file.time_update = info_of_file_or_dir.date_change
        # Save changes in db
        file.save()
        return file, False

    else:  # If is a directory
        if (move_flag):
            # Function to update a direcory
            dir, create_flag = instance_file_dir_rename_or_move(db.Directory, event.file_inode, event.ad_event_inode,
                                                                get_file_path(event.ad_event), parent_dir,
                                                                info_of_file_or_dir.date_change, info_of_file_or_dir)
        else:
            # Function to create a directory
            dir, create_flag = db_create_or_get_ins_file_or_dir_from_event(db.Directory, event.file_inode,
                                                                           get_file_path(event),
                                                                           parent_dir,
                                                                           info_of_file_or_dir)
        # Update all parents directory size
        update_parent_size(dir, info_of_file_or_dir.size, info_of_file_or_dir.date_change)
        # Save changes in db for parent directory
        parent_dir.save()
        if create_flag:
            dir.size = info_of_file_or_dir.size
        dir.time_update = info_of_file_or_dir.date_change
        # Save changes in db
        dir.save()
        return dir, True


def add_fs_event_to_db(event):
    # TODO : Need add exception handlers

    if event.ad_event: # Move or rename events
        inst, is_dir = update_instance_of_file_dir_model(event, True)
    else: # Create, change, delete events
        user = db_get_or_create_user(event.uid, event.uid_str)
        if event.evtype.type != "delete":
            inst, is_dir = update_instance_of_file_dir_model(event, False)
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

