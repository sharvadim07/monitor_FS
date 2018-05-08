import subprocess
import re

def uid_to_usr_str(uid):
    id_util_string = str(subprocess.check_output(['id', str(uid)]))
    if id_util_string:
        # uid = 1000(student)
        user_id_str = re.search(r'.*uid=[0-9]+[(]?(\w+)[)]?', id_util_string)
        if user_id_str:
            return user_id_str.groups()[0]
        else:
            return None