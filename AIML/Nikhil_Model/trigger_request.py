import requests
import json
import numpy as np
from json import JSONEncoder
import mysql.connector

import getopt, sys

class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


# Get full command-line arguments
full_cmd_arguments = sys.argv

# Keep all but the first
argument_list = full_cmd_arguments[1:]
res = list(map(float,argument_list))
print(res)
print(type(res))
print(argument_list)
print(type(argument_list))
data = [float(item) for item in argument_list]
print(data)

data1 = np.array(data,dtype=float).reshape(1,-1)

print(data1)

url = 'http://127.0.0.1:5000/api/'

#data = [[14.34, 1.68, 2.7, 25.0, 98.0, 2.8, 1.31, 0.53, 2.7, 13.0, 0.57, 1.96, 660.0]]
j_data = json.dumps(data1,cls=NumpyArrayEncoder)
headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
r = requests.post(url, data=j_data, headers=headers)
print(r, r.text)
