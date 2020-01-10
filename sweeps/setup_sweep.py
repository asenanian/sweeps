import os, os.path as path, shutil
import numbers
import numpy
import hashlib, json
import itertools

from .sweep_utils import get_timestamp

def init_dir(project_dir):
    dirs_to_make = [path.join(project_dir,dir) for dir in ['rfs','history','data']]
    [os.mkdir(dir) for dir in dirs_to_make if not path.exists(dir) ]
    if not path.exists(path.join(project_dir,'bin')):
        raise IOError("Bin directory missing, please include, and place scripts in it.")

def create_rfs(project_dir, sweep_file):
    """
    """
    # make sure directory is initialized
    init_dir(project_dir)

    sweep_filepath = path.join(project_dir,sweep_file)
    for rf, params in read_sweep(sweep_filepath):
        # write indiviual params of given rf to a params.json
        rf_path = path.join(project_dir,'rfs',rf)
        if not path.exists(rf_path):
            os.mkdir(rf_path)
            with open(path.join(rf_path,'params.json'), 'w+') as file:
                file.write(params)

            # make status.txt and log.txt files
            open(path.join(rf_path,'status.txt'),'w+').close()
            open(path.join(rf_path,'log.txt'),'w+').close()

    # copy sweeps file to a timestamped reference in history dir
    sweep = get_timestamp() + '.create.json'
    history_path = path.join(project_dir,'history')
    if not path.exists(history_path):
        os.mkdir(history_path)
    shutil.copyfile(sweep_filepath, path.join(history_path,sweep))

def delete_rfs(project_dir, sweep_file):
    sweep_filepath = path.join(project_dir,sweep_file)
    for rf,_ in read_sweep(sweep_filepath): #TODO: Check equality of params.json?
        rf_path = path.join(project_dir,'rfs',rf)
        if path.exists(rf_path):
            shutil.rmtree(rf_path)
    sweep = get_timestamp() + '.delete.json'
    history_path = path.join(project_dir,'history')
    if not path.exists(history_path):
        os.mkdir(history_path)
    shutil.copyfile(sweep_filepath, path.join(history_path,sweep))

def read_sweep(sweep_file):
    """
    Given a sweeps parameter file sweep_file, returns a generator producing a
    dictionary relating the rf to the splitted parameters.
    """
    with open(sweep_file) as file:
        sweep = json.load(file)

    # make handlers for given datatype
    dtype_handlers = dict()
    dtype_handlers['constant'] = lambda value : [value] if isinstance(value,numbers.Real)  \
                                                        else None
    dtype_handlers['manual'] = lambda value : value if isinstance(value,list) \
                                                    else None
    dtype_handlers['linspace'] = lambda value : numpy.linspace(*value).tolist() \
                                            if len(value) == 3 else None
    dtype_handlers['string'] = lambda value : [value]

    parameter_keys = list(sweep.keys())
    parameter_values = [dtype_handlers[item['sweep_type']](item['value'])  \
                                for item in sweep.values()]
    for index, value in enumerate(parameter_values):
        if value is None:
            raise ValueError("Value of parameter `" + str(parameter_keys[index]) + "` invalid")

    # make generator for rf : parameter
    for values in itertools.product(*parameter_values):
        params = dict(zip(parameter_keys,values))
        params = json.dumps(params,indent=4,sort_keys=True)
        rf = hashlib.md5(params.encode('utf-8')).hexdigest()[:16]
        yield (rf, params)
