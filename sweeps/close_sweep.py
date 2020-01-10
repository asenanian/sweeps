import os, os.path as path, shutil
import pandas as pd
import hashlib, json

from .setup_sweep import read_sweep

def close_rfs(project_dir, sweep_file):
    sweep_filepath = path.join(project_dir,sweep_file)
    rfs = [rf for rf,_ in read_sweep(sweep_filepath)]

    params = []
    results = []
    for rf in rfs:
        rf_path = path.join(project_dir,'rfs',rf)
        if path.exists(rf_path):
            with open(os.path.join(rf_path,'params.json')) as prm_fl:
                params.append(json.load(prm_fl))
    df = pd.DataFrame(params,index=rfs)

    with open(sweep_filepath) as file:
        sweep = json.load(file)
    params = json.dumps(sweep,indent=4,sort_keys=True)
    params_id = hashlib.md5(params.encode('utf-8')).hexdigest()[:16]
    data_path = path.join(project_dir,'data',params_id)
    if not path.exists(data_path):
        os.mkdir(data_path)



    df.to_pickle(path.join(data_path,'result.pkl'))
    shutil.copyfile(sweep_filepath,path.join(data_path,sweep_file))


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
    if directory_list:  # (if directory_list is not empty)
        warnings.warn("No recognized data type recognized; returning a file:")
        with open(os.path.join(sim_loc,'rfs',ID,directory_list[0])) as file:
            yield file
    else:
        raise IOError('No data files found for given run folder.')
