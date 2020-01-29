# sweeps
Run parameter sweeps easily, in parallel, with JSON parameters, logs, diverse language support, and parameter data frames.

## Installation
*Python **3.7** or above is required for running sweeps. Versions 3.6 and below will encounter error.*

To install: Download sweeps package, navigate to its directory (`cd sweeps`) and execute the following:
```bash
python setup.py install --user
```

After installation, `sweeps` may now be invoked from the command line anywhere on your system.

## Usage
This guide assumes you are working in the top-level of your parameter sweeps directory. For an example, see the directory tree below.
1. Initialize this directory by creating `bin` and `rfs` directories.
2. Add a JSON file to the top-level containing parameter sweep information.
⋅⋅* An example parameter sweep file, such as `sweep_config.json`, may be seen [in the test folder](https://github.com/brian-i/sweeps/blob/master/test/sweep.json).
3. Add a script file to the `bin` folder.
4. Run the script using `sweeps run` (below)

### To create rfs:
Run folders (rfs) represent individual runs of a script file for a particular parameter. The folder name is a hash depending on the parameter value and script file.

```bash
sweeps . create sweep_config.json
```

### To run script:
**Requirement:** A script file, such as `script.py`, must be located inside a `bin` folder on your top-level directory. (See example directory tree below:)
```bash
sweeps . run python script_file.py
```

### To query:
Querying shows the status of your run, including the number of rfs completed, queued, running, and failed.

**Requirement:** A script file, such as `script.py`, must be located inside a `bin` folder on your top-level directory. (This is already satisfied if `sweeps run` was used.)
```bash
sweeps . query script_file.py
```

### To close:
Closing produces finalizes a run by designating a directory within the `data` directory which
includes all parameter, log, and status information of the combined run. Additionally, it includes
a copy of the script and produces a pandas dataframe containing any data produced by your script organized by the parameters used for the data.

```bash
sweeps . close sweep_config.json
```

The following data have support for `sweeps . close`.
* HDF5 (.hdf5)
* Matlab (.mat)
* JSON (.json) *Note: Ensure that saved data file is not named params.json*
* Binary JSON (.bson)
* Numpy array (.npz)
* Python Pickel file (.pklz or .pkl)
* Julia, using HDF5 encoding (.jld or .jld2) (returns Numpy array if it is the only object stored in file, otherwise returns HDF5 keys)

Closing the sweep will find all data files from the above list produced by all completed runs of your script, and aggregate them within the dataframe. 

Here is a possible example of a dataframe produced by a script which, depending on the input parameters, produces one or two datafiles whos results are aggregated in a tuple:
```python
>>> import os
>>> import sweeps as sw
>>> cwd = os.getcwd()
>>> dataframes = sw.get_dataframe(cwd) # generator of dataframes for finished runs
>>> df = next(dataframes)
>>> df
                  a    b      c    results
e9b0f2081a509199  1  0.5    0.0          4
e9b0f2858a7b70b1  1  0.5   20.0  (4, 20.0)      # run produced two data files
a49e0b9b22f135a7  1  0.5   40.0          4
6648175135df5aec  1  0.5   60.0          4
f0a0ae3eaf59f41c  4  0.5    0.0          0
42aced5e6c241677  4  0.5   20.0  (0, 20.0)      # run produced two data files
c920026405b40f2d  4  0.5   40.0          0
a503c32641b59f8b  4  0.5   60.0          0
```


# Example Directory Structure Tree
```
.
├── bin
│   └── script_file.jl
├── history
│   ├── 2019-12-10_16-34-13.create.json
│   ├── 2019-12-10_16-34-40.run
│   └── 2019-12-10_16-34-40.script
├── rfs
│   ├── 0e37e95b8301883e
│   │   ├── log.txt
│   │   ├── params.json
│   │   ├── result1.pklz
│   │   ├── result2.pklz
│   │   └── status.txt
│   ├── 6e733249c3ae5dd1
│   │   ├── log.txt
│   │   ├── params.json
│   │   └── status.txt
│   ├── 7bfacd4db6a44d40
│   │   ├── log.txt
│   │   ├── params.json
│   │   ├── result1.pklz
│   │   └── status.txt
│   ├── 9ac81a2c5029aa08
│   │   ├── log.txt
│   │   ├── params.json
│   │   ├── result1.pklz
│   │   ├── result2.pklz
│   │   └── status.txt
│   └── d73ece6dc1a2f5e8
│       ├── log.txt
│       ├── params.json
│       ├── result1.pklz
│       └── status.txt
├── data
│   ├── eeab1386ca484886
│       ├── result.pkl
│       ├── sweep_config_copy.json
│       ├── script_file_copy.jl
└── sweep_config.json
```
