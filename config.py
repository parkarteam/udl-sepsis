import base64
import os

db_creds = {
'host' : 'mysql',
'user' : 'root',
'password' : 'Sepsis_Parkar_2020',
'database' : 'sepsis',
'auth_plugin' : 'mysql_native_password'
}

minio_creds = {
'host' : '13.67.138.157:8000',
'access_key' : 'opendatahub',
'secret_key' : 'b3BlbmRhdGFodWI=',
'bucketName' : 'sepsistest'
}

#Minio File locations

longitudnaljsonfile = '_longitudnalJsonFile.json'
vitalsignscsv = '_vitalsigns.csv'
labscsv = '_labs.csv'
demographiccsv = '_demographic.csv'

minio_prefix_labs = 'data_sepsis/delta_labs_files/'
minio_prefix_demographic = 'data_sepsis/delta_demographic_files/'
minio_prefix_vitalsigns = 'data_sepsis/delta_vitalsigns_files/'
minio_prefix_json = 'data_sepsis/json_files/'

#seldon endpoint
endpoint = "http://demo-classifier-lr-predictor.odh-sepsis.svc.cluster.local:8000/api/v1.0/predictions"

#Time frequency

frequency = 3
