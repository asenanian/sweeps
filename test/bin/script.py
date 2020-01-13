import time
import sys
import json
import pickle
import gzip
import os.path as path

rf = sys.argv[1]

with open(path.join(rf,'params.json')) as param_file:
    params = json.load(param_file)
a = params['a']
b = params['b']
c = params['c']

if a == 2: x = np.ones(3) # will throw exception. numpy not imported
elif a == 1: x = 4
else: x = 0

with gzip.open(path.join(rf,'result.pklz'),'wb') as f:
    pickle.dump(x,f,-1)

if c == 20: 
    with gzip.open(path.join(rf,'result2.pklz'),'wb') as f:
        pickle.dump(c,f,-1)