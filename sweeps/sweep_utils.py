import sys, os, os.path as path
import argparse
import datetime
import enum
import hashlib
import json

def read_params(rf,params=None):
    if params is None:
        with open(path.join(rf,'params.json')) as param_file:
            params = json.load(param_file)
    return argparse.Namespace(**params)

def get_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

def asheader(message, prefix="", length=80, line='-'):
    spaces = length - len(prefix) - len(message)
    n = spaces // 2
    return prefix + line*n + message + line*(spaces-n)

def write(file, message):
    file.flush()
    file.write(message+'\n')
    file.flush()

def get_script_id(script_file, project_dir):
    script_path = path.join(project_dir, "bin", script_file)
    with open(script_path) as file:
        contents = file.read()
        return script_file + "@" + hashlib.md5(contents.encode('utf-8')).hexdigest()


def get_param_id(project_dir,sweep_file):
    sweep_filepath = os.path.join(project_dir,sweep_file)
    with open(sweep_filepath) as file:
        sweep = json.load(file)
    params = json.dumps(sweep,indent=4,sort_keys=True)
    params_id = hashlib.md5(params.encode('utf-8')).hexdigest()[:16]
    return params_id

class Status(enum.Enum):
    RUNNING = 3
    QUEUED = 2
    FINISHED = 1
    FAILED = -1
    NEW = 0
    INVALID = 4

def generate_status(action, script_id):
    return " | ".join((action, get_timestamp(), script_id))

def check_status(rf, project_dir,script=None):
    with open(path.join(project_dir,'rfs',rf,'status.txt'), 'r') as file:
        status = Status.NEW
        for line in file:
            action, _, script_id = (s.strip() for s in line.split('|'))
            if script is not None: 
                if script_id != get_script_id(script,project_dir):
                    continue
            if status is Status.NEW:
                if action == "QUEUED":
                    status = Status.QUEUED
                else:
                    status = Status.INVALID
            elif status is Status.QUEUED:
                if action == "STARTED":
                    status = Status.RUNNING
                elif action == "KILLED":
                    status = Status.NEW
                else:
                    status = Status.INVALID
            elif status is Status.RUNNING:
                if action == "FINISHED":
                    status = Status.FINISHED
                elif action == "FAILED":
                    status = Status.FAILED
                else:
                    status = Status.INVALID
            elif status in (Status.FAILED, Status.FINISHED):
                if action == "QUEUED":
                    status = Status.QUEUED
                elif action == "KILLED":
                    status = status
                else:
                    status = Status.INVALID
    return status

def collect_rf_status(project_dir,rfs=None,script=None):
    status_table = {e : set() for e in Status}
    if rfs == None: 
        rfs = os.listdir(path.join(project_dir,'rfs'))
    for rf in rfs:
        if os.path.isdir(path.join(project_dir,'rfs',rf)):   # Check that path is a directory
            status = check_status(rf, project_dir, script)
            status_table[status].add(rf)
        else:
            if rf[0] != '.':    # Check if file is a hidden system file
                print('!! File', rf, 'in rfs directory is not a run folder. '
                    'It has been skipped.')
    return status_table

def query_status(script, project_dir):
    print("SWEEP SUMMARY: " + get_script_id(script, project_dir))
    for status,rfs in collect_rf_status(script,project_dir).items():
        print(str(status.name).rjust(13) + ": "
            + (str(len(rfs)) if len(rfs)>0 else "----").rjust(4))
