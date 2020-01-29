import os, os.path as path, shutil
import pandas as pd
import numpy as np
import math
import hashlib, json
import warnings

from .sweep_utils import Status, collect_rf_status, generate_status, write, get_param_id
from .setup_sweep import read_sweep


def close_rfs(project_dir, sweep_file):
    rfs = [rf for rf,_ in read_sweep(sweep_file)]
    rf_status = collect_rf_status(project_dir,rfs=rfs)

    if rf_status[Status.FAILED]:
        warnings.warn("Warning: Found rfs with status FAILED.")

    sweep_filepath = path.join(project_dir,sweep_file)
    finished_rfs = set(rf_status[Status.FINISHED])

    params = []
    results = []
    script_ids = []
    for rf in finished_rfs:
        rf_path = path.join(project_dir,'rfs',rf)
        if path.exists(rf_path):
            with open(os.path.join(rf_path,'params.json')) as param_file:
                params.append(json.load(param_file))
            tup = tuple([x for x in get_data(rf,project_dir)])
            if len(tup) == 1: 
                results.append(tup[0])
            elif len(tup) == 0: 
                warnings.warn("Data file was not produced by finished run: " + str(rf))
            else: 
                results.append(tup)
            with open(path.join(project_dir,'rfs',rf,'status.txt'), 'r') as file:
                for line in file:
                    _, _, script_id = (s.strip() for s in line.split('|'))
                script_ids.append(script_id)
    
    if np.unique(script_ids).size > 1: 
        raise ValueError("Reading data produced by a multiple scripts.")

    df = pd.DataFrame(params,index=finished_rfs)
    df['results'] = pd.Series(results,index=df.index)

    # designate directory for combined run results and information
    params_id = get_param_id(project_dir,sweep_file)
    data_path = path.join(project_dir,'data',params_id)
    if not path.exists(data_path):
        os.mkdir(data_path)

    # collect status file outputs and save to a master log file
    with open(path.join(data_path,'status.txt'),'w+') as status_file:
        for rf in rfs:
            with open(path.join(project_dir,'rfs',rf,'status.txt'),'r') as infile:
                for line in infile: pass
            write(status_file,"Status for RF " + str(rf) +": " + str(line))
    
    # collect log file outputs and save to a master log file
    with open(path.join(data_path,'log.txt'),'w+') as log_file:
        for rf in rfs:
            with open(path.join(project_dir,'rfs',rf,'log.txt'),'r') as infile:
                write(log_file,"LOG FILE FOR RF: " + str(rf))
                for line in infile: 
                    log_file.write(line)

    df.to_pickle(path.join(data_path,'result.pkl'))
    shutil.copyfile(sweep_filepath,path.join(data_path,sweep_file))

def get_dataframe(project_dir,rf=None):
    directory_list = os.listdir(os.path.join(project_dir,'data'))
    if rf == None:
        for param_folder in directory_list:
            yield pd.read_pickle(os.path.join(project_dir,'data',param_folder,'result.pkl'))
    else: 
        yield pd.read_pickle(os.path.join(project_dir,'data',rf,'result.pkl'))

def get_data(ID:str, sim_loc: str):
    """
    Return data extracted from a saved file in a particular run folder.

    Keyword arguments:
    ID -- hash / folder name of desired run
    sim_loc -- location of where sweeps was run and ./rfs/ folder is located
    """
    directory_list = os.listdir(os.path.join(sim_loc,'rfs',ID))
    directory_list = [e for e in directory_list if e not in (
        'log.txt', 'params.json', 'status.txt')]

    for filename in directory_list:
        if filename[0] == '.':
            # Hidden file - exclude from search
            directory_list.remove(filename)
            break
        filepath = os.path.join(sim_loc,'rfs',ID,filename)
        if filename[-5:] == '.hdf5':
            # HDF5 file
            import h5py
            with h5py.File(filepath, 'r') as f:
                print("Keys: %s" % f.keys())    # List all groups
                yield f
        elif filename[-4:] == '.mat':
            # Matlab matrix file
            import scipy.io
            yield scipy.io.loadmat(filepath)
        elif filename[-5:] == '.json' and filename != 'params.json':
            with open(filepath) as data_file:
                yield json.load(data_file)
        elif filename[-5:] == '.bson':
            # Binary JSON file
            import bson     # bson neds to be installed: pip install bson
            with open(filepath) as bson_file:
                yield bson.loads(bson_file.read())
        elif filename[-4:] == '.npz':
            # Numpy npz file
            yield np.load(filepath)
        elif filename[-5:] == '.pklz':
            # pickle file
            import pickle
            import gzip
            with gzip.open(filepath) as f:
                yield pickle.load(f)
        elif filename[-4:] == '.pkl':
            yield pd.read_pickle(filepath)
        elif filename[-4:] == '.jld' or filename[-5:] == '.jld2':
            # Julia JLD or JLD2 file, which uses HDF5 encoding
            # Return an appropriate numpy matrix if
            import h5py
            with h5py.File(filepath, 'r') as f:
                keys = f.keys()
                yield(
                    f if len(keys) > 1
                    else np.transpose(np.array(f.get(list(keys)[0])))
                    # Note: Julia stores data in column major order, as opposed
                    # to row major used by numpy, so to read matrices this way
                    # they are transposed.
                )
