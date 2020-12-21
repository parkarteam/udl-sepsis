# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 13:24:37 2020

@author: Prakash.Gore
"""


import mysql.connector


db_connection = mysql.connector.connect(
  host="mysql",
  user="sepsis",
  passwd="Success_2020",
  database="sepsis"
#  auth_plugin='mysql_native_password'
)


# creating database_cursor to perform SQL operation
db_cursor = db_connection.cursor()
# executing cursor with execute method and pass SQL query
student_sql_query = "INSERT INTO student(id,name) VALUES(01, 'John')"
#Get database table'
db_cursor.execute(student_sql_query)
db_connection.commit()
print(db_cursor.rowcount, "Record Inserted")
