import requests
import json
import sys
import time
import mysql.connector
import numpy as np
from json import JSONEncoder


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

PID = sys.argv[1]

bad_chars = ['[', '.', ']']

print("Sepsis detection for %s " %PID)

mydb = mysql.connector.connect(
    host="mysql",
    user="root",
    password="Sepsis_Parkar_2020",
    database="sepsis",
    auth_plugin='mysql_native_password'
)

cursor = mydb.cursor()
sql_select_query = """select Gender,hr,temp, age, O2Sat, sbp, resp, ICULOS,HospAdmTime from test where ICULOS = (select max(ICULOS) from test where pid= %s) and pid= %s"""

#cursor.execute("select Gender,hr,temp, age, O2Sat, sbp, resp, ICULOS,HospAdmTime from test where ICULOS = (select max(ICULOS) from test where pid='%PID') and pid='%PID';")
cursor.execute(sql_select_query,(PID,PID))

final_result = cursor.fetchall()
data = final_result
data1 = np.array(data).reshape(1,-1)
data2 = data1.tolist()
#print(type(data1))
#print(type(data2))
#print(data2[0][3])
timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
url = 'http://127.0.0.1:5000/api/'

filtered_columns = ['Gender', 'custom_hr', 'custom_temp','custom_age', 
                    'custom_o2stat', 'custom_bp','custom_resp' ,'ICULOS', 
                    'HospAdmTime']
                    
data = [[ 1 , 110 , 40.6 , 280 , 188 , 121 , 170 , 233 , -321.03 ]]
j_data = json.dumps(data1,cls=NumpyArrayEncoder)
headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
r = requests.post(url, data=j_data, headers=headers)
print(r, r.text)
sepsislabel = r.json()


sepsislabel = ''.join((filter(lambda i: i not in bad_chars, sepsislabel)))
#sepsislabel = int(sepsislabel)
print("SepsisLabel %s" %sepsislabel)
#print(type(sepsislabel))
sql = "INSERT INTO sepsis (PID ,SepsisLabel,Age,timestamp) VALUE ('%s','%s','%s','%s' );" % tuple([PID,sepsislabel,data2[0][3],timestamp])
cursor.execute(sql)
mydb.commit()
