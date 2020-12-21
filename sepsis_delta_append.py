# -*- coding: utf-8 -*-
"""
Created on Mon Oct 12 15:38:30 2020

@author: Prakash.Gore
"""


import mysql.connector
from minio import Minio
from itertools import groupby
import itertools
import csv
import json
import glob
import os
import math
import time
import requests
from datetime import date
from datetime import datetime

from config import *

file=open('udl_script.log', 'w')
#endpoint = "http://demo-classifier-lr-predictor.odh-sepsis.svc.cluster.local:8000/api/v1.0/predictions"
current_timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

def date_diff_in_seconds(dt2, dt1):
    timedelta = dt2 - dt1
    return timedelta.seconds/60

def validate_string(val):
   if val != None:
        if type(val) is int:
            return str(val).encode('utf-8')
        else:
            return val

def calculateAge(birthDate): 
	today = date.today() 
	age = today.year - birthDate.year
	return age 

def returnSex(Gender):
    if Gender == 'M':
        return "Male"
    elif Gender == 'F':
        return "Female"
    else :
        return "NA"
def returnGender(Gender):
    if Gender == 1:
        return "Male"
    elif Gender == 0:
        return "Female"
    else :
        return "NA"
    
def returnSexInt(Gender):
    if Gender == 'M':
        return 1
    elif Gender == 'F':
        return 0
    else :
        return "NA"
    
mydb = mysql.connector.connect(
    host=db_creds['host'],
    user=db_creds['user'],
    password=db_creds['password'],
    database=db_creds['database'],
    auth_plugin=db_creds['auth_plugin']
)

cursor = mydb.cursor()

client = Minio(minio_creds['host'], access_key=minio_creds['access_key'], secret_key=minio_creds['secret_key'], secure=False)
objects_labs = client.list_objects(minio_creds['bucketName'], prefix=minio_prefix_labs, recursive=True)
objects_demographic = client.list_objects(minio_creds['bucketName'], prefix=minio_prefix_demographic, recursive=True)
objects_vitalsigns = client.list_objects(minio_creds['bucketName'], prefix=minio_prefix_vitalsigns, recursive=True)
objects_json = client.list_objects(minio_creds['bucketName'], prefix=minio_prefix_json, recursive=True)

print(objects_labs)
for (obj_json) in (objects_json):
    json_name = os.path.basename(obj_json.object_name)
    json_name1 = os.path.splitext(json_name)[0]
    splitResult = json_name1.split( "_" )
    json_pid_filename = splitResult[0]
    json_filename = splitResult[1]
    json_data = client.get_object(minio_creds['bucketName'], obj_json.object_name)
    with open(json_name, 'wb') as file_data:
        for d_json in json_data.stream(32*1024):
            file_data.write(d_json)


for (obj_demographic) in (objects_demographic):
    demographic_name = os.path.basename(obj_demographic.object_name)
    demographic_data = client.get_object(minio_creds['bucketName'], obj_demographic.object_name)
    with open(demographic_name, 'wb') as file_data:
        for d_demographic in demographic_data.stream(32*1024):
            file_data.write(d_demographic)
            
    

for (obj_vitalsigns, obj_labs) in itertools.zip_longest( objects_vitalsigns, objects_labs):
    vitalsigns_file_date = obj_vitalsigns.last_modified
    vitalsigns_file_date = vitalsigns_file_date.replace(tzinfo=None)
    current_time = datetime.now()
    diff = date_diff_in_seconds(current_time, vitalsigns_file_date)
    vitalsign_name = os.path.basename(obj_vitalsigns.object_name)
    vitalsign_name1 = os.path.splitext(vitalsign_name)[0]
    splitResult = vitalsign_name1.split( "_" )
    vitalsign_pid_filename = splitResult[0]
    vitalsign_filename = splitResult[1]
    vitalsign_json_name = vitalsign_pid_filename + longitudnaljsonfile
    
    print(type(obj_labs),obj_labs)
    
    print(obj_labs.object_name)
    print(obj_labs.last_modified)
    labs_file_date = obj_labs.last_modified
    labs_file_date = labs_file_date.replace(tzinfo=None)
    current_time = datetime.now()
    labs_name = os.path.basename(obj_labs.object_name)
    labs_name1 = os.path.splitext(labs_name)[0]
    splitResult = labs_name1.split( "_" )
    labs_pid_filename = splitResult[0]
    labs_filename = splitResult[1]
    labs_json_name = labs_pid_filename + longitudnaljsonfile
    diff1 = date_diff_in_seconds(current_time, labs_file_date)

    vitalsign_data = client.get_object(minio_creds['bucketName'], obj_vitalsigns.object_name)

    with open(vitalsign_pid_filename + vitalsignscsv, 'wb') as file_data:
        for d in vitalsign_data.stream(32*1024):
            file_data.write(d)

    labs_data = client.get_object(minio_creds['bucketName'], obj_labs.object_name)
    with open(labs_pid_filename + labscsv, 'wb') as file_data:
        for d in labs_data.stream(32*1024):
            file_data.write(d)
            
    # import pdb
    # pdb.set_trace()
    if os.path.isfile(vitalsign_json_name):
        with open(vitalsign_json_name, 'rb') as json_data:
            output = json.load(json_data)
    else:
        output = {'Demographic': [],'Vital_Signs':[],'labs':[]}
        with open(vitalsign_pid_filename + demographiccsv, 'r') as csv_demographic:
            r = csv.DictReader(csv_demographic)
            data_demographic = [dict(d) for d in r]
            
        def keyfunc(x):
            return x['Patient_id']
        
        for k, g in groupby(data_demographic, lambda r: (r['Patient_id'], r['DOB'],r['Gender'],r['Unit1'],r['Unit2'],r['HospAdmTime'])):
            output['Demographic'].append({
                "Patient_id": k[0],
                "Age" :str(k[1]),
                "Gender":str(k[2]),
                "Unit1":str(k[3]),
                "Unit2":str(k[4]),
                "HospAdmTime":str(k[5])
                })
            
        with open(vitalsign_pid_filename + longitudnaljsonfile, 'w') as outfile:
            outfile.write(json.dumps(output, indent=4))
             

    Demographic = output["Demographic"]
    Demographic = dict(Demographic[0])
    Age = str(validate_string(Demographic['Age']))
    Gender = str(validate_string(Demographic['Gender']))
    Unit1 = str(validate_string(Demographic['Unit1']))
    Unit2 = str(validate_string(Demographic['Unit2']))
    HospAdmTime = str(validate_string(Demographic['HospAdmTime']))
   # print(Demographic)
    Age = datetime.strptime(Age, '%Y-%m-%d')

  
            
    if (vitalsign_pid_filename==labs_pid_filename and  diff < frequency and diff1 < frequency):
        with open(vitalsign_json_name, 'rb') as json_data:
            output = json.load(json_data)
        with open(vitalsign_pid_filename + vitalsignscsv, 'r') as csv_vital_signs:
            r = csv.DictReader(csv_vital_signs)
            data_vital_signs = [dict(d) for d in r]
    
        for k, g in groupby(data_vital_signs, lambda r: (r['Time'], r['HR'],r['O2Sat'],r['Temp'],r['SBP'],r['MAP'],r['DBP'],r['Resp'],r['EtCO2'],r['ICULOS'])):
            output['Vital_Signs'].append({  
                    "Time": k[0],
                    "HR" :str(k[1]),
                    "O2Sat" :str(k[2]),
                    "Temp" :str(k[3]),
                    "SBP" :str(k[4]),
                    "MAP" :str(k[5]),
                    "DBP" :str(k[6]),
                    "Resp" :str(k[7]),
                    "EtCO2":str(k[8]),
                    "ICULOS":str(k[9])
            })
            Vital_Signs_Array = [returnSexInt(Gender),float(k[1]),float(k[3]),calculateAge(Age),float(k[2]),float(k[4]),float(k[7]),float(k[9]),float(HospAdmTime)]
            Vital_Signs_Array = [0 if math.isnan(x) else x for x in Vital_Signs_Array]
            Vital_Signs_Array = [Vital_Signs_Array]
            print(Vital_Signs_Array)
            json_data = {"data":{"ndarray":Vital_Signs_Array}}
            response = requests.post(endpoint,json=json_data)
            r=response.json()
            SepsisLabel=int(r['data']['ndarray'][0])
            print( " Sepsis detected %s " % int(r['data']['ndarray'][0]) )
            sql = "INSERT INTO sepsis (PID ,Gender, Time,HR, Temp,Age,  O2Sat, SBP,Resp ,ICULOS,HospAdmTime,SepsisLabel,DetectedTime) VALUE ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' );" % tuple([vitalsign_pid_filename,returnGender(Vital_Signs_Array[0][0]),k[0],Vital_Signs_Array[0][1],Vital_Signs_Array[0][2],Vital_Signs_Array[0][3],Vital_Signs_Array[0][4],Vital_Signs_Array[0][5],Vital_Signs_Array[0][6],Vital_Signs_Array[0][7],Vital_Signs_Array[0][8],SepsisLabel,current_timestamp])
            cursor.execute(sql)
            mydb.commit()
            
        with open(vitalsign_json_name, 'w') as outfile:
            outfile.write(json.dumps(output, indent=4))
        
  
        with open(labs_json_name, 'rb') as json_data:
            output = json.load(json_data)

        with open(labs_pid_filename + labscsv, 'r') as csv_labs:
            r = csv.DictReader(csv_labs)
            data_labs = [dict(d) for d in r]
            
        for k, g in groupby(data_labs, lambda r: (r['Time'], r['BaseExcess'],r['HCO3'],r['FiO2'],r['pH'],r['PaCO2'],r['SaO2'],r['AST'],r['BUN'],r['Alkalinephos'],r['Calcium'],r['Chloride'],r['Creatinine'],r['Bilirubin_direct'],r['Glucose'],r['Lactate'],r['Magnesium'],r['Phosphate'],r['Potassium'],r['Bilirubin_total'],r['TroponinI'],r['Hct'],r['Hgb'],r['PTT'],r['WBC'],r['Fibrinogen'],r['Platelets'])):
            output['labs'].append({  
                    "Time": k[0],
                    "BaseExcess" :str(k[1]),
                    "HCO3":str(k[2]),
                    "FiO2": str(k[3]),
                    "pH" :str(k[4]),
                    "PaCO2":str(k[5]),
                    "SaO2": str(k[6]),
                    "AST" :str(k[7]),
                    "BUN":str(k[8]),
                    "Alkalinephos": str(k[9]),
                    "Calcium" :str(k[10]),
                    "Chloride":str(k[11]),
                    "Creatinine": str(k[12]),
                    "Bilirubin_direct" :str(k[13]),
                    "Glucose":str(k[14]),
                    "Lactate": str(k[15]),
                    "Magnesium" :str(k[16]),
                    "Phosphate":str(k[17]),
                    "Potassium" :str(k[18]),
                    "Bilirubin_total":str(k[19]),
                    "TroponinI": str(k[20]),
                    "Hct" :str(k[21]),
                    "Hgb":str(k[22]),
                    "PTT":str(k[23]),
                    "WBC": str(k[24]),
                    "Fibrinogen" :str(k[25]),
                    "Platelets":str(k[26])
            })
        with open(labs_json_name, 'w') as outfile:
            outfile.write(json.dumps(output, indent=4))
        

        f1 = open(vitalsign_pid_filename + vitalsignscsv)
        csv_data_vitalsigns = csv.reader(f1)
        print(csv_data_vitalsigns)
        f3 = open(vitalsign_pid_filename + vitalsignscsv)
        csv_data_vitalsigns1 = csv.reader(f3)
        lines=0
        lines= len(list(csv_data_vitalsigns1))
        f3.close()

        f2 = open(labs_pid_filename + labscsv)
        csv_data_labs = csv.reader(f2)
        print(csv_data_labs)
        f4 = open(labs_pid_filename + labscsv)
        csv_data_labs1 = csv.reader(f4)
        f4.close()
        header = next(csv_data_vitalsigns)
        header = next(csv_data_labs)# This skips the first row of the CSV file. 
    

        counter = 0
        #print(csv_data_vitalsigns)
        #print(csv_data_labs)
        for (obj_vitalsigns, obj_labs) in itertools.zip_longest(csv_data_vitalsigns, csv_data_labs):
            
            print(obj_vitalsigns)
            print(obj_labs)

            counter += 1
            sql = "INSERT INTO patient (PID  ,HR  ,O2Sat  ,Temp  ,SBP  ,MAP  ,DBP  ,Resp  ,EtCO2  ,BaseExcess  ,HCO3  ,FiO2  ,pH  ,PaCO2  ,SaO2  ,AST  ,BUN  ,Alkalinephos  ,Calcium  ,Chloride  ,Creatinine  ,Bilirubin_direct  ,Glucose  ,Lactate  ,Magnesium  ,Phosphate  ,Potassium  ,Bilirubin_total  ,TroponinI  ,Hct  ,Hgb  ,PTT  ,WBC  ,Fibrinogen  ,Platelets,Age,Gender,Unit1,Unit2,HospAdmTime,ICULOS ) VALUE (%(PID)s,%(HR)s,%(O2Sat)s,%(Temp)s,%(SBP)s,%(MAP)s,%(DBP)s,%(Resp)s,%(EtCO2)s,%(BaseExcess)s,%(HCO3)s,%(FiO2)s,%(pH)s,%(PaCO2)s,%(SaO2)s,%(AST)s,%(BUN)s,%(Alkalinephos)s,%(Calcium)s,%(Chloride)s,%(Creatinine)s,%(Bilirubin_direct)s,%(Glucose)s,%(Lactate)s,%(Magnesium)s,%(Phosphate)s,%(Potassium)s,%(Bilirubin_total)s,%(TroponinI)s,%(Hct)s,%(Hgb)s,%(PTT)s,%(WBC)s,%(Fibrinogen)s,%(Platelets)s,%(Age)s,%(Gender)s,%(Unit1)s,%(Unit2)s,%(HospAdmTime)s,%(ICULOS)s)"
            param_dict = {"PID": obj_vitalsigns[1], "HR": obj_vitalsigns[2],"O2Sat": obj_vitalsigns[3],"Temp": obj_vitalsigns[4],"SBP": obj_vitalsigns[5],"MAP": obj_vitalsigns[6],"DBP": obj_vitalsigns[7],"Resp": obj_vitalsigns[8],"EtCO2": obj_vitalsigns[9],"BaseExcess": obj_labs[2],"HCO3": obj_labs[3],"FiO2": obj_labs[4],"pH": obj_labs[5],"PaCO2": obj_labs[6],"SaO2": obj_labs[7],"AST": obj_labs[8],"BUN": obj_labs[9],"Alkalinephos": obj_labs[10],"Calcium": obj_labs[11],"Chloride": obj_labs[12],"Creatinine": obj_labs[13],"Bilirubin_direct": obj_labs[14],"Glucose": obj_labs[15],"Lactate": obj_labs[16],"Magnesium": obj_labs[17],"Phosphate": obj_labs[18],"Potassium": obj_labs[19],"Bilirubin_total": obj_labs[20],"TroponinI": obj_labs[21],"Hct": obj_labs[22],"Hgb": obj_labs[23] ,"PTT": obj_labs[24],"WBC": obj_labs[25],"Fibrinogen": obj_labs[26],"Platelets": obj_labs[27],"Age":calculateAge(Age), "Gender":returnSex(Gender),"Unit1":Unit1, "Unit2":Unit2,"HospAdmTime":HospAdmTime,"ICULOS":obj_vitalsigns[10]   }
            cursor.execute(sql,param_dict)
        f1.close()
        f2.close()
        mydb.commit()
#        if counter > lines:
#            break
        json_name = vitalsign_json_name
        client.fput_object(minio_creds['bucketName'], minio_prefix_json+json_name,json_name)
    elif (diff < frequency):
        with open(vitalsign_json_name, 'rb') as json_data:
            output = json.load(json_data)
        with open(vitalsign_pid_filename + vitalsignscsv, 'r') as csv_vital_signs:
            r = csv.DictReader(csv_vital_signs)
            data_vital_signs = [dict(d) for d in r]
                
        for k, g in groupby(data_vital_signs, lambda r: (r['Time'], r['HR'],r['O2Sat'],r['Temp'],r['SBP'],r['MAP'],r['DBP'],r['Resp'],r['EtCO2'],r['ICULOS'])):
            output['Vital_Signs'].append({  
                    "Time": k[0],
                    "HR" :str(k[1]),
                    "O2Sat" :str(k[2]),
                    "Temp" :str(k[3]),
                    "SBP" :str(k[4]),
                    "MAP" :str(k[5]),
                    "DBP" :str(k[6]),
                    "Resp" :str(k[7]),
                    "EtCO2":str(k[8]),
                    "ICULOS":str(k[9])
            })
            Vital_Signs_Array = [returnSexInt(Gender),float(k[1]),float(k[3]),calculateAge(Age),float(k[2]),float(k[4]),float(k[7]),float(k[9]),float(HospAdmTime)]
            Vital_Signs_Array = [0 if math.isnan(x) else x for x in Vital_Signs_Array]
            Vital_Signs_Array = [Vital_Signs_Array]
            print(Vital_Signs_Array)
            json_data = {"data":{"ndarray":Vital_Signs_Array}}
            response = requests.post(endpoint,json=json_data)
            r=response.json()
            SepsisLabel=int(r['data']['ndarray'][0])
            print("Sepsis detected %s " % int(r['data']['ndarray'][0]))
            sql = "INSERT INTO sepsis (PID ,Gender, Time,HR, Temp,Age,  O2Sat, SBP,Resp ,ICULOS,HospAdmTime,SepsisLabel,DetectedTime) VALUE ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' );" % tuple([vitalsign_pid_filename,returnGender(Vital_Signs_Array[0][0]),k[0],Vital_Signs_Array[0][1],Vital_Signs_Array[0][2],Vital_Signs_Array[0][3],Vital_Signs_Array[0][4],Vital_Signs_Array[0][5],Vital_Signs_Array[0][6],Vital_Signs_Array[0][7],Vital_Signs_Array[0][8],SepsisLabel,current_timestamp])
            cursor.execute(sql)
            mydb.commit()
            
        with open(vitalsign_json_name, 'w') as outfile:
            outfile.write(json.dumps(output, indent=4))
        value = ''
        fv = open(vitalsign_pid_filename + vitalsignscsv)
        csv_data_vitalsigns = csv.reader(fv)
        next(csv_data_vitalsigns)
        for row in csv_data_vitalsigns:
            sql = "INSERT INTO patient (PID  ,HR  ,O2Sat  ,Temp  ,SBP  ,MAP  ,DBP  ,Resp  ,EtCO2,BaseExcess  ,HCO3  ,FiO2  ,pH  ,PaCO2  ,SaO2  ,AST  ,BUN  ,Alkalinephos  ,Calcium  ,Chloride  ,Creatinine  ,Bilirubin_direct  ,Glucose  ,Lactate  ,Magnesium  ,Phosphate  ,Potassium  ,Bilirubin_total  ,TroponinI  ,Hct  ,Hgb  ,PTT  ,WBC  ,Fibrinogen  ,Platelets,Age,Gender,Unit1,Unit2,HospAdmTime) VALUE ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' );" % tuple([row[1], row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,value,calculateAge(Age),returnSex(Gender),Unit1,Unit2,HospAdmTime])
            cursor.execute(sql)
            mydb.commit()
        fv.close()
        json_name = vitalsign_json_name
        client.fput_object(minio_creds['bucketName'], minio_prefix_json+json_name,json_name)

    elif (diff1 < frequency):

        with open(labs_json_name, 'rb') as json_data:
            output = json.load(json_data)

        with open(labs_pid_filename + labscsv, 'r') as csv_labs:
            r = csv.DictReader(csv_labs)
            data_labs = [dict(d) for d in r]
            
        for k, g in groupby(data_labs, lambda r: (r['Time'], r['BaseExcess'],r['HCO3'],r['FiO2'],r['pH'],r['PaCO2'],r['SaO2'],r['AST'],r['BUN'],r['Alkalinephos'],r['Calcium'],r['Chloride'],r['Creatinine'],r['Bilirubin_direct'],r['Glucose'],r['Lactate'],r['Magnesium'],r['Phosphate'],r['Potassium'],r['Bilirubin_total'],r['TroponinI'],r['Hct'],r['Hgb'],r['PTT'],r['WBC'],r['Fibrinogen'],r['Platelets'])):
            output['labs'].append({  
                    "Time": k[0],
                    "BaseExcess" :str(k[1]),
                    "HCO3":str(k[2]),
                    "FiO2": str(k[3]),
                    "pH" :str(k[4]),
                    "PaCO2":str(k[5]),
                    "SaO2": str(k[6]),
                    "AST" :str(k[7]),
                    "BUN":str(k[8]),
                    "Alkalinephos": str(k[9]),
                    "Calcium" :str(k[10]),
                    "Chloride":str(k[11]),
                    "Creatinine": str(k[12]),
                    "Bilirubin_direct" :str(k[13]),
                    "Glucose":str(k[14]),
                    "Lactate": str(k[15]),
                    "Magnesium" :str(k[16]),
                    "Phosphate":str(k[17]),
                    "Potassium" :str(k[18]),
                    "Bilirubin_total":str(k[19]),
                    "TroponinI": str(k[20]),
                    "Hct" :str(k[21]),
                    "Hgb":str(k[22]),
                    "PTT":str(k[23]),
                    "WBC": str(k[24]),
                    "Fibrinogen" :str(k[25]),
                    "Platelets":str(k[26])
            })
        with open(labs_json_name, 'w') as outfile:
            outfile.write(json.dumps(output, indent=4))
        value = ''
        fl = open(labs_pid_filename + labscsv)
        csv_data_labs = csv.reader(fl)
        header = next(csv_data_labs)
        for row in csv_data_labs:
            sql = "INSERT INTO patient (PID, HR  ,O2Sat  ,Temp  ,SBP  ,MAP  ,DBP  ,Resp  ,EtCO2, BaseExcess  ,HCO3  ,FiO2  ,pH  ,PaCO2  ,SaO2  ,AST  ,BUN  ,Alkalinephos  ,Calcium  ,Chloride  ,Creatinine  ,Bilirubin_direct  ,Glucose  ,Lactate  ,Magnesium  ,Phosphate  ,Potassium  ,Bilirubin_total  ,TroponinI  ,Hct  ,Hgb  ,PTT  ,WBC  ,Fibrinogen  ,Platelets,Age,Gender,Unit1,Unit2,HospAdmTime,ICULOS ) VALUE ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" % tuple([row[1],value,value,value,value,value,value,value,value, row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17],row[18],row[19],row[20],row[21],row[22],row[23],row[24],row[25],row[26],row[27],calculateAge(Age),returnSex(Gender),Unit1,Unit2,HospAdmTime,row[0]])
            cursor.execute(sql)
            mydb.commit()        
        fl.close()
        json_name = labs_json_name
        client.fput_object(minio_creds['bucketName'], minio_prefix_json+json_name,json_name)

files = glob.glob('p0*', recursive=True)
for f in files:
    try:
        os.remove(f)
    except OSError as e:
        print("Error: %s : %s" % (f, e.strerror))
print("New Script Completed")


