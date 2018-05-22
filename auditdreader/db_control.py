import db
import general
import logging



def get_file_path(event):
    if event.file_name[0] == '/':
        return  event.file_name
    elif event.file_name[0] == '.':
        return event.dir_path + general.name_from_path(event.file_name)
    else:
        return event.dir_path + "/" + event.file_name

# 5-member tuple with the following contents:
# uid, inode , isdir, size, date of change
def get_info_by_event(event):
    info_of_file_or_dir = general.get_file_info(get_file_path(event))
    if info_of_file_or_dir[1] != event.file_inode:
        logging.warning("File or directory path name " + get_file_path(event), \
                        " is not match with inode " + event.file_inode)
        raise FileNotFoundError
    return info_of_file_or_dir

def db_create_or_get_ins_file_or_dir_from_event( db_model, event_inode, event_path, event_parent = None, info = None ):
    instance_of_model_file_dir = db_model.get_or_none(
        inode=event_inode
    )
    create_flag = False
    if not instance_of_model_file_dir:
        create_flag = True
        # 5-member tuple with the following contents:
        # uid, inode , isdir, size, date of modify
        if info:
            file_dir_info = info
        else:
            file_dir_info = general.get_file_info(event_path)
            if file_dir_info[1] != event_inode:
                logging.warning("Path ", file_dir_info[1] +
                                " is not match with inode " + event_inode)
                raise FileNotFoundError
        # Create new instance
        instance_of_model_file_dir = db_model.create(inode=event_inode)
        # Set owner
        instance_of_model_file_dir.owner = db_get_or_create_user(file_dir_info[0],
                                                                 general.uid_to_usr_str(file_dir_info[0]))
        # Set name
        name = general.name_from_path(event_path)
        if not name:
            logging.warning("Name will not set, inode:" + str(event_inode))
            return -1
        instance_of_model_file_dir.name = name
        # Set initial size 0
        instance_of_model_file_dir.size = 0
        # Set time update
        instance_of_model_file_dir.time_update = file_dir_info[4]
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
    :return: return db instance (file or directory) and flag Is a directory or not
    """
    parent_dir = None
    info_of_file_or_dir = None
    if(move_flag):
        parent_dir, create_flag = db_create_or_get_ins_file_or_dir_from_event(db.Directory,
                                                                    event.ad_event.dir_inode, event.ad_event.dir_path)
        info_of_file_or_dir = get_info_by_event(event.ad_event)
    else:
        parent_dir, create_flag  = db_create_or_get_ins_file_or_dir_from_event(db.Directory, event.dir_inode, event.dir_path)
        info_of_file_or_dir = get_info_by_event(event)

    if not info_of_file_or_dir[2]:  # If is a file
        if (move_flag):
            # Function to update a file
            file, create_flag = instance_file_dir_rename_or_move(db.File, event.file_inode, event.ad_event_inode,
                                                                 get_file_path(event.ad_event), parent_dir,
                                                                 info_of_file_or_dir[4], info_of_file_or_dir)
        else:
            # Function to create a file
            file, create_flag = db_create_or_get_ins_file_or_dir_from_event(db.File, event.file_inode,
                                                                            get_file_path(event),
                                                                            parent_dir,
                                                                            info_of_file_or_dir)
        # Update all parents directory size
        update_file_parent_size(create_flag, file, info_of_file_or_dir[3], info_of_file_or_dir[4])
        file.size = info_of_file_or_dir[3]
        file.time_update = info_of_file_or_dir[4]
        #file.save()
        return file, False

    else:  # If is a directory
        if (move_flag):
            # Function to update a direcory
            dir, create_flag = instance_file_dir_rename_or_move(db.Directory, event.file_inode, event.ad_event_inode,
                                                                get_file_path(event.ad_event), parent_dir,
                                                                info_of_file_or_dir[4], info_of_file_or_dir)
        else:
            # Function to create a directory
            dir, create_flag = db_create_or_get_ins_file_or_dir_from_event(db.Directory, event.file_inode,
                                                                           get_file_path(event),
                                                                           parent_dir,
                                                                           info_of_file_or_dir)
        # Update all parents directory size
        update_parent_size(dir, info_of_file_or_dir[3], info_of_file_or_dir[4])
        if create_flag:
            dir.size = info_of_file_or_dir[3]
        dir.time_update = info_of_file_or_dir[4]
        #dir.save()
        return dir, True

def add_fs_event_to_db(event):
    # TODO : Need add exception handler

    if event.ad_event: # Move or rename events
        inst, is_dir = update_instance_of_file_dir_model(event, True)
    else: # Create, change, delete events
        user = db_get_or_create_user(event.uid, event.uid_str)
        if event.evtype.type != "delete":
            inst, is_dir = update_instance_of_file_dir_model(event, False)
            inst.save()
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

